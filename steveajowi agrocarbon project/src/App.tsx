import { useEffect, useState, type FormEvent } from 'react';
import {
    complianceStandards,
    farmDevices,
    farms,
    measurements,
    projectObjectives,
    tokenBatches,
    verificationDataRequired,
    verificationItems,
} from './data';
import type { Farm } from './types';
import './styles.css';

const statusTone: Record<string, string> = {
    baseline: 'Baseline',
    monitoring: 'Monitoring',
    verified: 'Verified',
};

const toneTone: Record<'leaf' | 'earth' | 'sun' | 'sky', string> = {
    leaf: 'leaf',
    earth: 'earth',
    sun: 'sun',
    sky: 'sky',
};

const pipeline = [
    {
        title: 'Monitor',
        detail: 'Collect DBH, height, soil, weather, and GPS evidence from the field.',
        state: 'active',
    },
    {
        title: 'Report',
        detail: 'Normalize measurements and convert them into a carbon accounting record.',
        state: 'active',
    },
    {
        title: 'Verify',
        detail: 'Route the evidence pack to an independent reviewer for approval.',
        state: 'active',
    },
    {
        title: 'Tokenize',
        detail: 'Mint or list ACT credits after verification is signed off.',
        state: 'ready',
    },
] as const;

const initialFarmForm = {
    name: '',
    owner: '',
    location: '',
    hectares: '',
    treesPlanted: '',
    species: '',
};

const initialMeasurementForm = {
    farmId: farms[0].id,
    metric: '',
    value: '',
    source: '',
};

const initialVerificationForm = {
    label: '',
    note: '',
};

type WorkspaceRole = 'farmer' | 'verifier' | 'admin';

interface ActivityEntry {
    id: string;
    action: string;
    detail: string;
    timestamp: string;
}

interface AuthSession {
    displayName: string;
    role: WorkspaceRole;
    signedInAt: string;
}

const roleConfigurations: Record<WorkspaceRole, { label: string; summary: string; focus: string; actions: string[] }> = {
    farmer: {
        label: 'Farmer workspace',
        summary: 'Capture field activity, maintain farm records, and prepare evidence for review.',
        focus: 'Field operations, data capture, and farm readiness.',
        actions: ['Add a farm', 'Log a measurement', 'Queue a verification request'],
    },
    verifier: {
        label: 'Verifier workspace',
        summary: 'Review evidence packs, check completeness, and mark items for approval.',
        focus: 'Evidence quality, audit trail, and verification status.',
        actions: ['Review checklist items', 'Inspect measurements', 'Approve token batches'],
    },
    admin: {
        label: 'Admin workspace',
        summary: 'Monitor the full MRV pipeline, manage records, and export report bundles.',
        focus: 'Project oversight, reporting, and token lifecycle management.',
        actions: ['Export MRV bundle', 'Reset demo data', 'Queue token batch'],
    },
};

const rolePermissions: Record<WorkspaceRole, {
    showFarmForms: boolean;
    showMeasurementLog: boolean;
    showVerificationForm: boolean;
    showFarmRegistry: boolean;
    showCompliance: boolean;
    showTokenLedger: boolean;
    showAdminExport: boolean;
    showActivityTrail: boolean;
}> = {
    farmer: {
        showFarmForms: true,
        showMeasurementLog: true,
        showVerificationForm: true,
        showFarmRegistry: true,
        showCompliance: false,
        showTokenLedger: false,
        showAdminExport: false,
        showActivityTrail: false,
    },
    verifier: {
        showFarmForms: false,
        showMeasurementLog: true,
        showVerificationForm: true,
        showFarmRegistry: true,
        showCompliance: true,
        showTokenLedger: false,
        showAdminExport: false,
        showActivityTrail: true,
    },
    admin: {
        showFarmForms: true,
        showMeasurementLog: true,
        showVerificationForm: true,
        showFarmRegistry: true,
        showCompliance: true,
        showTokenLedger: true,
        showAdminExport: true,
        showActivityTrail: true,
    },
};

function downloadTextFile(fileName: string, content: string, mimeType: string) {
    if (typeof window === 'undefined') {
        return;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download = fileName;
    link.click();

    window.URL.revokeObjectURL(url);
}

const STORAGE_KEY = 'ajowi-agrocarbon-mrv-state';
const AUTH_KEY = 'ajowi-agrocarbon-auth-session';

type PersistedState = {
    farms: typeof farms;
    measurements: typeof measurements;
    verificationItems: typeof verificationItems;
    tokenBatches: typeof tokenBatches;
    activityLog: ActivityEntry[];
    reviewedMeasurementIds: string[];
};

function loadPersistedState(): PersistedState | null {
    if (typeof window === 'undefined') {
        return null;
    }

    const rawState = window.localStorage.getItem(STORAGE_KEY);

    if (!rawState) {
        return null;
    }

    try {
        return JSON.parse(rawState) as PersistedState;
    } catch {
        return null;
    }
}

function loadAuthSession(): AuthSession | null {
    if (typeof window === 'undefined') {
        return null;
    }

    const rawSession = window.localStorage.getItem(AUTH_KEY);

    if (!rawSession) {
        return null;
    }

    try {
        return JSON.parse(rawSession) as AuthSession;
    } catch {
        return null;
    }
}

function App() {
    const persistedState = loadPersistedState();
    const persistedSession = loadAuthSession();
    const [authSession, setAuthSession] = useState<AuthSession | null>(persistedSession);
    const [loginForm, setLoginForm] = useState<{ displayName: string; role: WorkspaceRole }>({
        displayName: persistedSession?.displayName ?? '',
        role: persistedSession?.role ?? 'admin',
    });

    const [farmRecords, setFarmRecords] = useState(persistedState?.farms ?? farms);
    const [measurementRecords, setMeasurementRecords] = useState(persistedState?.measurements ?? measurements);
    const [verificationRecords, setVerificationRecords] = useState(
        persistedState?.verificationItems ?? verificationItems,
    );
    const [tokenRecords, setTokenRecords] = useState(persistedState?.tokenBatches ?? tokenBatches);
    const [activityLog, setActivityLog] = useState<ActivityEntry[]>(persistedState?.activityLog ?? []);
    const [reviewedMeasurementIds, setReviewedMeasurementIds] = useState<string[]>(persistedState?.reviewedMeasurementIds ?? []);
    const [farmForm, setFarmForm] = useState(initialFarmForm);
    const [measurementForm, setMeasurementForm] = useState(initialMeasurementForm);
    const [verificationForm, setVerificationForm] = useState(initialVerificationForm);
    const [farmQuery, setFarmQuery] = useState('');
    const [measurementQuery, setMeasurementQuery] = useState('');
    const latestActivity = activityLog[0] ?? null;

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        if (authSession) {
            window.localStorage.setItem(AUTH_KEY, JSON.stringify(authSession));
            return;
        }

        window.localStorage.removeItem(AUTH_KEY);
    }, [authSession]);

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        const nextState: PersistedState = {
            farms: farmRecords,
            measurements: measurementRecords,
            verificationItems: verificationRecords,
            tokenBatches: tokenRecords,
            activityLog,
            reviewedMeasurementIds,
        };

        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    }, [activityLog, farmRecords, measurementRecords, verificationRecords, tokenRecords, reviewedMeasurementIds]);

    const currentFarm = farmRecords[0] ?? farms[0];
    const totalHectares = farmRecords.reduce((sum, farm) => sum + farm.hectares, 0).toFixed(1);
    const totalTrees = farmRecords.reduce((sum, farm) => sum + farm.treesPlanted, 0).toLocaleString();
    const verifiedFarms = farmRecords.filter((farm) => farm.status === 'verified').length;
    const mintedTokens = tokenRecords.filter((batch) => batch.state === 'Minted').length;
    const pendingVerifications = verificationRecords.filter((item) => item.status === 'pending').length;
    const evidenceItems = verificationDataRequired.length + farmDevices.length;
    const readinessPercentage = farmRecords.length > 0 ? Math.round((verifiedFarms / farmRecords.length) * 100) : 0;
    const verificationQueuePercentage = verificationRecords.length > 0
        ? Math.round(((verificationRecords.length - pendingVerifications) / verificationRecords.length) * 100)
        : 0;
    const sessionStartedLabel = authSession ? new Date(authSession.signedInAt).toLocaleString() : '';
    const farmStatusCounts = {
        baseline: farmRecords.filter((farm) => farm.status === 'baseline').length,
        monitoring: farmRecords.filter((farm) => farm.status === 'monitoring').length,
        verified: farmRecords.filter((farm) => farm.status === 'verified').length,
    };
    const farmPulse = farmRecords.map((farm) => {
        const parsedSignal = Number.parseFloat(farm.soilCarbonChange.replace(/[^0-9.-]/g, ''));

        return {
            name: farm.name,
            shortName: farm.name
                .split(' ')
                .slice(0, 2)
                .join(' '),
            status: farm.status,
            signal: Number.isNaN(parsedSignal) ? 0 : parsedSignal,
        };
    });
    const activityTrend = Array.from({ length: 5 }, (_, index) => {
        const date = new Date();
        date.setDate(date.getDate() - (4 - index));

        const count = activityLog.filter((entry) => new Date(entry.timestamp).toDateString() === date.toDateString()).length;

        return {
            label: date.toLocaleDateString(undefined, { weekday: 'short' }),
            count,
        };
    });
    const measurementTrend = Array.from({ length: 5 }, (_, index) => {
        const date = new Date();
        date.setDate(date.getDate() - (4 - index));

        const count = measurementRecords.filter((measurement) => new Date(measurement.capturedAt).toDateString() === date.toDateString()).length;

        return {
            label: date.toLocaleDateString(undefined, { weekday: 'short' }),
            count,
        };
    });
    const measurementFreshness = (capturedAt: string) => {
        const capturedDate = new Date(capturedAt);
        const dayDiff = Math.floor((Date.now() - capturedDate.getTime()) / (1000 * 60 * 60 * 24));

        if (dayDiff <= 0) {
            return 'Captured today';
        }

        if (dayDiff === 1) {
            return 'Captured 1 day ago';
        }

        return `Captured ${dayDiff} days ago`;
    };

    const handleReviewLatestMeasurement = () => {
        if (!latestMeasurement || reviewedMeasurementIds.includes(latestMeasurement.id)) {
            return;
        }

        const latestFarmName = farmRecords.find((farm) => farm.id === latestMeasurement.farmId)?.name ?? 'selected farm';

        setReviewedMeasurementIds((currentIds) => [latestMeasurement.id, ...currentIds]);
        pushActivity('Measurement reviewed', `${latestMeasurement.metric} for ${latestFarmName}`);
    };
    const verificationStatusCounts = {
        complete: verificationRecords.filter((item) => item.status === 'complete').length,
        pending: verificationRecords.filter((item) => item.status === 'pending').length,
    };
    const verificationCompletionRatio = verificationRecords.length > 0
        ? Math.round((verificationStatusCounts.complete / verificationRecords.length) * 100)
        : 0;
    const activeRole = authSession?.role ?? loginForm.role;
    const roleConfig = roleConfigurations[activeRole];
    const roleView = rolePermissions[activeRole];
    const filteredFarmRecords = farmRecords.filter((farm) => {
        const searchTarget = `${farm.name} ${farm.owner} ${farm.location} ${farm.species.join(' ')}`.toLowerCase();
        return searchTarget.includes(farmQuery.trim().toLowerCase());
    });
    const filteredMeasurementRecords = measurementRecords.filter((measurement) => {
        const farmName = farmRecords.find((farm) => farm.id === measurement.farmId)?.name ?? '';
        const searchTarget = `${farmName} ${measurement.metric} ${measurement.value} ${measurement.source}`.toLowerCase();
        return searchTarget.includes(measurementQuery.trim().toLowerCase());
    });
    const latestMeasurement = measurementRecords[0] ?? null;
    const reviewedMeasurementCount = reviewedMeasurementIds.length;
    const pendingMeasurementCount = Math.max(measurementRecords.length - reviewedMeasurementCount, 0);

    const getFarmStatusDetails = (status: Farm['status']) => {
        const nextReviewDate = new Date();

        if (status === 'verified') {
            nextReviewDate.setDate(nextReviewDate.getDate() + 30);
            return {
                label: 'Verified asset',
                detail: 'Review window closes in 30 days',
                dueDateLabel: `Next review ${nextReviewDate.toLocaleDateString()}`,
                note: 'Verification pack is ready for export or tokenization.',
            };
        }

        if (status === 'monitoring') {
            nextReviewDate.setDate(nextReviewDate.getDate() + 7);
            return {
                label: 'Active monitoring',
                detail: 'Next field check due in 7 days',
                dueDateLabel: `Next review ${nextReviewDate.toLocaleDateString()}`,
                note: 'Keep measurements flowing so the record stays fresh.',
            };
        }

        nextReviewDate.setDate(nextReviewDate.getDate() + 14);

        return {
            label: 'Baseline only',
            detail: 'Schedule first verification review',
            dueDateLabel: `Next review ${nextReviewDate.toLocaleDateString()}`,
            note: 'No token-ready evidence yet; field capture should continue.',
        };
    };

    const verificationRoadmap = verificationRecords.map((item, index) => {
        const stepNumber = index + 1;
        const reviewDate = new Date();

        reviewDate.setDate(reviewDate.getDate() + stepNumber * 3);

        return {
            ...item,
            stepNumber,
            reviewLabel: item.status === 'complete' ? 'Ready to approve' : 'Awaiting reviewer attention',
            reviewDateLabel: item.status === 'complete' ? 'Available now' : `Review target ${reviewDate.toLocaleDateString()}`,
        };
    });

    const pushActivity = (action: string, detail: string) => {
        setActivityLog((currentLog) => [
            {
                id: `activity-${Date.now()}-${currentLog.length + 1}`,
                action,
                detail,
                timestamp: new Date().toISOString(),
            },
            ...currentLog,
        ].slice(0, 12));
    };

    const handleLogin = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!loginForm.displayName.trim()) {
            return;
        }

        const nextSession: AuthSession = {
            displayName: loginForm.displayName.trim(),
            role: loginForm.role,
            signedInAt: new Date().toISOString(),
        };

        setAuthSession(nextSession);
        pushActivity('Workspace opened', `${nextSession.displayName} signed in as ${nextSession.role}`);
    };

    const handleLogout = () => {
        pushActivity('Workspace closed', `${authSession?.displayName ?? 'User'} signed out`);
        setAuthSession(null);
        if (typeof window !== 'undefined') {
            window.localStorage.removeItem(AUTH_KEY);
        }
    };

    const reportSnapshot = {
        project: 'Ajowi AgroCarbon Token',
        generatedAt: new Date().toISOString(),
        session: authSession
            ? {
                displayName: authSession.displayName,
                role: authSession.role,
                signedInAt: authSession.signedInAt,
            }
            : null,
        summary: {
            farms: farmRecords.length,
            hectares: totalHectares,
            trees: totalTrees,
            verifiedFarms,
            pendingVerifications,
            mintedTokens,
            reviewedMeasurements: reviewedMeasurementCount,
            pendingMeasurements: pendingMeasurementCount,
        },
        farms: farmRecords,
        measurements: measurementRecords,
        verificationItems: verificationRecords,
        tokenBatches: tokenRecords,
        activityLog,
        reviewedMeasurementIds,
        verificationInputs: verificationDataRequired,
        farmDevices,
        complianceStandards,
        projectObjectives,
    };

    if (!authSession) {
        return (
            <div className="app-shell login-shell">
                <div className="ambient ambient-one" />
                <div className="ambient ambient-two" />

                <section className="login-card">
                    <div className="login-hero">
                        <p className="eyebrow">Ajowi AgroCarbon Token</p>
                        <h1>Secure MRV workspace access</h1>
                        <p>
                            Sign in locally to open the farm, verifier, or admin workspace. This gate keeps the
                            dashboard focused on the right MRV actions for each user type.
                        </p>

                        <div className="login-role-grid">
                            {Object.values(roleConfigurations).map((config) => (
                                <article className="login-role-card" key={config.label}>
                                    <h4>{config.label}</h4>
                                    <p>{config.summary}</p>
                                </article>
                            ))}
                        </div>
                    </div>

                    <form className="login-form" onSubmit={handleLogin}>
                        <h2>Enter workspace</h2>
                        <label>
                            Display name
                            <input
                                value={loginForm.displayName}
                                onChange={(event) => setLoginForm((current) => ({ ...current, displayName: event.target.value }))}
                                placeholder="Your name"
                            />
                        </label>
                        <label>
                            Workspace role
                            <select
                                value={loginForm.role}
                                onChange={(event) => setLoginForm((current) => ({ ...current, role: event.target.value as WorkspaceRole }))}
                            >
                                <option value="farmer">Farmer</option>
                                <option value="verifier">Verifier</option>
                                <option value="admin">Admin</option>
                            </select>
                        </label>
                        <button type="submit" className="primary-btn">Enter workspace</button>
                        <p className="login-note">
                            This is a local session for the prototype. Replace it with real authentication when the backend is ready.
                        </p>
                    </form>
                </section>
            </div>
        );
    }

    const handleFarmSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!farmForm.name.trim() || !farmForm.owner.trim() || !farmForm.location.trim()) {
            return;
        }

        const nextFarm = {
            id: `farm-${String(farmRecords.length + 1).padStart(3, '0')}`,
            name: farmForm.name.trim(),
            owner: farmForm.owner.trim(),
            location: farmForm.location.trim(),
            hectares: Number(farmForm.hectares) || 0,
            treesPlanted: Number(farmForm.treesPlanted) || 0,
            species: farmForm.species
                .split(',')
                .map((item) => item.trim())
                .filter(Boolean),
            status: 'monitoring' as const,
            coordinates: 'To be mapped',
            soilCarbonChange: 'Awaiting baseline',
            lastUpdated: 'Just now',
        };

        setFarmRecords((currentRecords) => [nextFarm, ...currentRecords]);
        setFarmForm(initialFarmForm);
        pushActivity('Farm created', `${nextFarm.name} in ${nextFarm.location}`);
    };

    const handleMeasurementSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!measurementForm.metric.trim() || !measurementForm.value.trim() || !measurementForm.source.trim()) {
            return;
        }

        const nextMeasurement = {
            id: `m-${String(measurementRecords.length + 1).padStart(3, '0')}`,
            farmId: measurementForm.farmId,
            metric: measurementForm.metric.trim(),
            value: measurementForm.value.trim(),
            source: measurementForm.source.trim(),
            capturedAt: new Date().toISOString().slice(0, 10),
        };

        setMeasurementRecords((currentRecords) => [nextMeasurement, ...currentRecords]);
        setMeasurementForm(initialMeasurementForm);
        pushActivity('Measurement logged', `${nextMeasurement.metric} for ${farmRecords.find((farm) => farm.id === nextMeasurement.farmId)?.name ?? 'selected farm'}`);
    };

    const handleVerificationSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!verificationForm.label.trim()) {
            return;
        }

        setVerificationRecords((currentRecords) => [
            {
                label: verificationForm.label.trim(),
                note: verificationForm.note.trim() || 'Queued for verifier review',
                status: 'pending',
            },
            ...currentRecords,
        ]);

        setVerificationForm(initialVerificationForm);
        pushActivity('Verification queued', verificationForm.label.trim());
    };

    const handleGenerateTokenBatch = () => {
        const baseCredits = currentFarm.hectares ? (currentFarm.hectares * 8.2).toFixed(1) : '0.0';
        const reviewSummary = `${reviewedMeasurementCount} reviewed, ${pendingMeasurementCount} pending measurements`;

        const nextToken = {
            farm: currentFarm.name,
            credits: `${baseCredits} tCO2e`,
            tokenId: `ACT-2026-${String(tokenRecords.length + 18).padStart(5, '0')}`,
            state: 'Pending mint' as const,
        };

        setTokenRecords((currentRecords) => [nextToken, ...currentRecords]);
        pushActivity('Token batch queued', `${nextToken.tokenId} for ${nextToken.farm} · ${reviewSummary}`);
    };

    const handleResetDemoData = () => {
        setFarmRecords(farms);
        setMeasurementRecords(measurements);
        setVerificationRecords(verificationItems);
        setTokenRecords(tokenBatches);
        setActivityLog([]);
        setReviewedMeasurementIds([]);
        setFarmForm(initialFarmForm);
        setMeasurementForm(initialMeasurementForm);
        setVerificationForm(initialVerificationForm);

        if (typeof window !== 'undefined') {
            window.localStorage.removeItem(STORAGE_KEY);
        }
    };

    const handleDownloadReport = () => {
        downloadTextFile(
            `ajowi-agrocarbon-mrv-report-${new Date().toISOString().slice(0, 10)}.json`,
            JSON.stringify(reportSnapshot, null, 2),
            'application/json',
        );
    };

    return (
        <div className="app-shell">
            <div className="ambient ambient-one" />
            <div className="ambient ambient-two" />

            <header className="topbar">
                <div>
                    <p className="eyebrow">Ajowi AgroCarbon Token</p>
                    <h1>MRV workspace for farm-level carbon verification</h1>
                </div>
                <div className="topbar-actions">
                    <div className="topbar-user">
                        <div className="user-chip">
                            <span className="dot" />
                            {authSession.displayName} · {roleConfig.label}
                        </div>
                        <button type="button" className="ghost-btn" onClick={handleLogout}>
                            Sign out
                        </button>
                    </div>
                    <div className="topbar-badge">
                        <span className="dot" />
                        Private prototype
                    </div>
                </div>
            </header>

            <section className="workspace-rail" aria-label="Workspace status">
                <article className="workspace-rail-card">
                    <span>Signed in user</span>
                    <strong>{authSession.displayName}</strong>
                    <p>{roleConfig.label}</p>
                </article>
                <article className="workspace-rail-card">
                    <span>Recommended action</span>
                    <strong>{roleConfig.actions[0]}</strong>
                    <p>{roleConfig.focus}</p>
                </article>
                <article className="workspace-rail-card">
                    <span>Current evidence</span>
                    <strong>{evidenceItems} inputs</strong>
                    <p>{pendingVerifications} checks still pending</p>
                </article>
                <article className="workspace-rail-card">
                    <span>Workspace state</span>
                    <strong>Local + exportable</strong>
                    <p>Session started {sessionStartedLabel}</p>
                </article>
            </section>

            <section className="hero-card">
                <div className="hero-copy">
                    <p className="section-label">Project snapshot</p>
                    <h2>A single dashboard to track farms, measurements, verifier evidence, and ACT token issuance.</h2>
                    <p className="hero-text">
                        This MVP gives the client a working interface for the workflow described in the MRV document: capture
                        field evidence, organize review, calculate credits, and prepare verified batches for tokenization.
                    </p>
                    <div className="role-summary-card">
                        <div>
                            <p className="section-label">{roleConfig.label}</p>
                            <h3>{roleConfig.summary}</h3>
                            <p>{roleConfig.focus}</p>
                        </div>
                        <ul>
                            {roleConfig.actions.map((action) => (
                                <li key={action}>{action}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="hero-actions">
                        <button type="button" className="primary-btn">Open farm registry</button>
                        <button type="button" className="secondary-btn">Review verification queue</button>
                        <button type="button" className="ghost-btn" onClick={handleDownloadReport}>
                            Download MRV bundle
                        </button>
                        {roleView.showAdminExport ? (
                            <button type="button" className="ghost-btn" onClick={handleResetDemoData}>
                                Reset demo data
                            </button>
                        ) : null}
                    </div>
                    <div className="hero-metrics">
                        <div>
                            <span>Evidence inputs</span>
                            <strong>{evidenceItems}</strong>
                        </div>
                        <div>
                            <span>Pending verifier checks</span>
                            <strong>{pendingVerifications}</strong>
                        </div>
                        <div>
                            <span>Minted token batches</span>
                            <strong>{mintedTokens}</strong>
                        </div>
                    </div>
                </div>

                <div className="stats-grid">
                    <article>
                        <span>Registered farms</span>
                        <strong>{farmRecords.length}</strong>
                        <div className="stat-chart" aria-hidden="true">
                            <div className="stat-chart-bar tone-earth" style={{ flexGrow: Math.max(farmStatusCounts.baseline, 1) }} />
                            <div className="stat-chart-bar tone-leaf" style={{ flexGrow: Math.max(farmStatusCounts.monitoring, 1) }} />
                            <div className="stat-chart-bar tone-sky" style={{ flexGrow: Math.max(farmStatusCounts.verified, 1) }} />
                        </div>
                    </article>
                    <article>
                        <span>Total hectares</span>
                        <strong>{totalHectares}</strong>
                        <div className="stat-chart stat-chart-slim" aria-hidden="true">
                            {farmRecords.map((farm) => (
                                <div
                                    className={`stat-chart-bar ${farm.status === 'verified' ? 'tone-sky' : farm.status === 'monitoring' ? 'tone-leaf' : 'tone-earth'}`}
                                    key={`${farm.id}-hectares`}
                                    style={{ flexGrow: Math.max(farm.hectares, 0.5) }}
                                />
                            ))}
                        </div>
                    </article>
                    <article>
                        <span>Total trees</span>
                        <strong>{totalTrees}</strong>
                        <div className="stat-chart stat-chart-slim" aria-hidden="true">
                            {farmRecords.map((farm) => (
                                <div
                                    className={`stat-chart-bar ${farm.status === 'verified' ? 'tone-sky' : farm.status === 'monitoring' ? 'tone-leaf' : 'tone-earth'}`}
                                    key={`${farm.id}-trees`}
                                    style={{ flexGrow: Math.max(farm.treesPlanted / 1000, 0.5) }}
                                />
                            ))}
                        </div>
                    </article>
                    <article>
                        <span>Verified farms</span>
                        <strong>{verifiedFarms}</strong>
                        <div className="stat-chart" aria-hidden="true">
                            <div className="stat-chart-bar tone-sky" style={{ flexGrow: Math.max(verifiedFarms, 1) }} />
                            <div className="stat-chart-bar tone-earth" style={{ flexGrow: Math.max(farmRecords.length - verifiedFarms, 1) }} />
                        </div>
                    </article>
                    <article>
                        <span>Signed in as</span>
                        <strong>{authSession.displayName}</strong>
                        <p>{roleConfig.label} since {sessionStartedLabel}</p>
                    </article>
                </div>
            </section>

            <section className="panel panel-full">
                <div className="panel-heading">
                    <div>
                        <p className="section-label">Report snapshot</p>
                        <h3>What the current MRV package contains</h3>
                    </div>
                </div>

                <div className="snapshot-grid">
                    <article className="snapshot-card">
                        <span>Farm records</span>
                        <strong>{farmRecords.length}</strong>
                        <p>Registered project sites ready for monitoring and review.</p>
                    </article>
                    <article className="snapshot-card">
                        <span>Evidence items</span>
                        <strong>{evidenceItems}</strong>
                        <p>Verification inputs and farm devices surfaced in the bundle.</p>
                    </article>
                    <article className="snapshot-card">
                        <span>Measurement reviews</span>
                        <strong>{reviewedMeasurementCount}/{measurementRecords.length}</strong>
                        <p>{pendingMeasurementCount} items still waiting on review.</p>
                    </article>
                    <article className="snapshot-card">
                        <span>Token batches</span>
                        <strong>{tokenRecords.length}</strong>
                        <p>ACT batches waiting to be minted, listed, or audited.</p>
                    </article>
                    <article className="snapshot-card">
                        <span>Status</span>
                        <strong>Local + exportable</strong>
                        <p>Records persist in the browser and can be downloaded as JSON.</p>
                    </article>
                </div>

                <div className="section-divider" />

                <div className="role-workspace-grid">
                    <article className="role-workspace-card">
                        <span>Current mode</span>
                        <strong>{roleConfig.label}</strong>
                        <p>{roleConfig.focus}</p>
                    </article>
                    <article className="role-workspace-card">
                        <span>Next action</span>
                        <strong>{roleConfig.actions[0]}</strong>
                        <p>{roleConfig.actions[1]}</p>
                    </article>
                    <article className="role-workspace-card">
                        <span>Export ready</span>
                        <strong>JSON bundle</strong>
                        <p>Download the current MRV package for sharing or handoff.</p>
                    </article>
                </div>

                <div className="priority-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="section-label">Today&apos;s priorities</p>
                            <h3>What should happen next in this workspace</h3>
                        </div>
                    </div>

                    <div className="priority-grid">
                        <article className="priority-card">
                            <h4>Workflow progress</h4>
                            <p>Verified farms are the clearest signal of MRV maturity right now.</p>
                            <div className="progress-meter" aria-label="MRV readiness">
                                <div className="progress-meter-bar" style={{ width: `${readinessPercentage}%` }} />
                            </div>
                            <strong>{readinessPercentage}% ready</strong>
                            <span>{verifiedFarms} of {farmRecords.length} farms verified</span>
                        </article>

                        <article className="priority-card">
                            <h4>Action queue</h4>
                            <ul className="priority-list">
                                {roleConfig.actions.map((action) => (
                                    <li key={action}>{action}</li>
                                ))}
                            </ul>
                        </article>

                        <article className="priority-card">
                            <h4>Verification health</h4>
                            <p>{verificationRecords.length - pendingVerifications} items cleared from the queue.</p>
                            <div className="progress-meter progress-meter-secondary" aria-label="Verification completion">
                                <div className="progress-meter-bar" style={{ width: `${verificationQueuePercentage}%` }} />
                            </div>
                            <strong>{verificationQueuePercentage}% complete</strong>
                            <span>{pendingVerifications} items still waiting on review</span>
                        </article>
                    </div>
                </div>

                <div className="panel-heading">
                    <div>
                        <p className="section-label">Project objectives</p>
                        <h3>What the client is actually trying to achieve</h3>
                    </div>
                </div>

                <div className="highlight-grid">
                    {projectObjectives.map((item) => (
                        <article className={`highlight-card tone-${toneTone[item.tone]}`} key={item.title}>
                            <h4>{item.title}</h4>
                            <p>{item.description}</p>
                        </article>
                    ))}
                </div>
            </section>

            <main className="content-grid">
                {roleView.showFarmRegistry ? (
                    <section className="panel panel-large">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Farm registry</p>
                                <h3>Field assets and carbon readiness</h3>
                                <p className="panel-subtitle">
                                    Showing {filteredFarmRecords.length} of {farmRecords.length} farms
                                </p>
                            </div>
                            <span className="panel-note">Demo data only</span>
                        </div>

                        <div className="panel-tools">
                            <label className="tool-field">
                                Search farms
                                <input
                                    value={farmQuery}
                                    onChange={(event) => setFarmQuery(event.target.value)}
                                    placeholder="Search by name, owner, location, or species"
                                />
                            </label>
                        </div>

                        <div className="farm-pulse-panel">
                            <div className="farm-pulse-header">
                                <div>
                                    <span>Farm pulse</span>
                                    <strong>Soil carbon signal by site</strong>
                                </div>
                                <p>Higher bars indicate stronger carbon gain in the current snapshot.</p>
                            </div>

                            <div className="farm-pulse-chart" aria-label="Farm soil carbon pulse">
                                {farmPulse.map((farm) => (
                                    <article className="farm-pulse-bar" key={farm.name}>
                                        <span>{farm.shortName}</span>
                                        <div className="farm-pulse-track">
                                            <div
                                                className={`farm-pulse-fill status-${farm.status}`}
                                                style={{ height: `${Math.max(farm.signal * 140, 22)}px` }}
                                            />
                                        </div>
                                        <strong>{farm.signal > 0 ? `+${farm.signal.toFixed(2)}` : farm.signal.toFixed(2)}</strong>
                                    </article>
                                ))}
                            </div>
                        </div>

                        <div className="farm-list">
                            {filteredFarmRecords.length > 0 ? filteredFarmRecords.map((farm) => {
                                const statusDetails = getFarmStatusDetails(farm.status);

                                return (
                                    <article className={`farm-card farm-card-${farm.status}`} key={farm.id}>
                                        <div className="farm-card-header">
                                            <div>
                                                <h4>{farm.name}</h4>
                                                <p>{farm.owner}</p>
                                            </div>
                                            <span className={`status-pill status-${farm.status}`}>{statusTone[farm.status]}</span>
                                        </div>

                                        <div className="farm-status-block">
                                            <strong>{statusDetails.label}</strong>
                                            <p>{statusDetails.detail}</p>
                                            <span className="farm-status-due">{statusDetails.dueDateLabel}</span>
                                            <span>{statusDetails.note}</span>
                                        </div>

                                        <dl className="farm-meta">
                                            <div>
                                                <dt>Location</dt>
                                                <dd>{farm.location}</dd>
                                            </div>
                                            <div>
                                                <dt>Area</dt>
                                                <dd>{farm.hectares} ha</dd>
                                            </div>
                                            <div>
                                                <dt>Trees</dt>
                                                <dd>{farm.treesPlanted.toLocaleString()}</dd>
                                            </div>
                                            <div>
                                                <dt>GPS</dt>
                                                <dd>{farm.coordinates}</dd>
                                            </div>
                                        </dl>

                                        <div className="chip-row">
                                            {farm.species.map((species) => (
                                                <span className="chip" key={species}>{species}</span>
                                            ))}
                                        </div>

                                        <p className="farm-footer">
                                            Soil signal: <strong>{farm.soilCarbonChange}</strong>{' '}
                                            <span>• Updated {farm.lastUpdated}</span>
                                        </p>
                                    </article>
                                );
                            }) : (
                                <div className="empty-search">No farms match the current search.</div>
                            )}
                        </div>
                    </section>
                ) : null}

                <aside className="panel side-panel">
                    <div className="panel-heading">
                        <div>
                            <p className="section-label">MRV pipeline</p>
                            <h3>Workflow from monitoring to tokenization</h3>
                        </div>
                    </div>

                    <div className="pipeline">
                        {pipeline.map((step, index) => (
                            <div className="pipeline-step" key={step.title}>
                                <div className={`step-index ${step.state}`}>{index + 1}</div>
                                <div>
                                    <h4>{step.title}</h4>
                                    <p>{step.detail}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="panel-callout">
                        <p className="section-label">Current focus farm</p>
                        <h4>{currentFarm.name}</h4>
                        <p>{currentFarm.location}</p>
                        <div className="callout-grid">
                            <span><strong>{currentFarm.hectares}</strong> ha</span>
                            <span><strong>{currentFarm.treesPlanted.toLocaleString()}</strong> trees</span>
                            <span><strong>{currentFarm.status}</strong></span>
                        </div>
                    </div>

                    <div className="panel-callout panel-callout-soft">
                        <p className="section-label">Review readiness</p>
                        <h4>{reviewedMeasurementCount}/{measurementRecords.length} measurements reviewed</h4>
                        <p>{pendingMeasurementCount === 0 ? 'Tokenization can reference a fully reviewed measurement set.' : `${pendingMeasurementCount} measurements still need review before minting is fully traceable.`}</p>
                    </div>

                    <div className="mini-actions">
                        {roleView.showTokenLedger ? (
                            <>
                                <button type="button" className="secondary-btn" onClick={handleGenerateTokenBatch}>
                                    Queue token batch
                                </button>
                                <span className="mini-action-note">
                                    {reviewedMeasurementCount} reviewed / {pendingMeasurementCount} pending
                                </span>
                            </>
                        ) : null}
                    </div>
                </aside>

                {roleView.showFarmForms || roleView.showMeasurementLog || roleView.showVerificationForm ? (
                    <section className="panel panel-large control-panel">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Control center</p>
                                <h3>Capture new project activity</h3>
                            </div>
                            <span className="panel-note">Local state only</span>
                        </div>

                        <div className="control-grid">
                            {roleView.showFarmForms ? (
                                <form className="form-card" onSubmit={handleFarmSubmit}>
                                    <h4>Add farm</h4>
                                    <label>
                                        Farm name
                                        <input
                                            value={farmForm.name}
                                            onChange={(event) => setFarmForm((current) => ({ ...current, name: event.target.value }))}
                                            placeholder="Ajowi South Block"
                                        />
                                    </label>
                                    <label>
                                        Owner
                                        <input
                                            value={farmForm.owner}
                                            onChange={(event) => setFarmForm((current) => ({ ...current, owner: event.target.value }))}
                                            placeholder="Farmer name"
                                        />
                                    </label>
                                    <label>
                                        Location
                                        <input
                                            value={farmForm.location}
                                            onChange={(event) => setFarmForm((current) => ({ ...current, location: event.target.value }))}
                                            placeholder="County, country"
                                        />
                                    </label>
                                    <div className="form-row">
                                        <label>
                                            Hectares
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.1"
                                                value={farmForm.hectares}
                                                onChange={(event) => setFarmForm((current) => ({ ...current, hectares: event.target.value }))}
                                                placeholder="10.5"
                                            />
                                        </label>
                                        <label>
                                            Trees planted
                                            <input
                                                type="number"
                                                min="0"
                                                value={farmForm.treesPlanted}
                                                onChange={(event) => setFarmForm((current) => ({ ...current, treesPlanted: event.target.value }))}
                                                placeholder="1200"
                                            />
                                        </label>
                                    </div>
                                    <label>
                                        Species, comma separated
                                        <input
                                            value={farmForm.species}
                                            onChange={(event) => setFarmForm((current) => ({ ...current, species: event.target.value }))}
                                            placeholder="Grevillea, Mango, Sesbania"
                                        />
                                    </label>
                                    <button type="submit" className="primary-btn">Create farm record</button>
                                </form>
                            ) : null}

                            {roleView.showMeasurementLog ? (
                                <form className="form-card" onSubmit={handleMeasurementSubmit}>
                                    <h4>Log measurement</h4>
                                    <label>
                                        Farm
                                        <select
                                            value={measurementForm.farmId}
                                            onChange={(event) => setMeasurementForm((current) => ({ ...current, farmId: event.target.value }))}
                                        >
                                            {farmRecords.map((farm) => (
                                                <option key={farm.id} value={farm.id}>{farm.name}</option>
                                            ))}
                                        </select>
                                    </label>
                                    <label>
                                        Metric
                                        <input
                                            value={measurementForm.metric}
                                            onChange={(event) => setMeasurementForm((current) => ({ ...current, metric: event.target.value }))}
                                            placeholder="Soil carbon"
                                        />
                                    </label>
                                    <label>
                                        Value
                                        <input
                                            value={measurementForm.value}
                                            onChange={(event) => setMeasurementForm((current) => ({ ...current, value: event.target.value }))}
                                            placeholder="2.18%"
                                        />
                                    </label>
                                    <label>
                                        Source
                                        <input
                                            value={measurementForm.source}
                                            onChange={(event) => setMeasurementForm((current) => ({ ...current, source: event.target.value }))}
                                            placeholder="Field sensor or lab"
                                        />
                                    </label>
                                    <button type="submit" className="secondary-btn">Save measurement</button>
                                </form>
                            ) : null}

                            {roleView.showVerificationForm ? (
                                <form className="form-card" onSubmit={handleVerificationSubmit}>
                                    <h4>Submit verifier request</h4>
                                    <label>
                                        Checklist item
                                        <input
                                            value={verificationForm.label}
                                            onChange={(event) => setVerificationForm((current) => ({ ...current, label: event.target.value }))}
                                            placeholder="Boundary polygon review"
                                        />
                                    </label>
                                    <label>
                                        Note
                                        <textarea
                                            rows={4}
                                            value={verificationForm.note}
                                            onChange={(event) => setVerificationForm((current) => ({ ...current, note: event.target.value }))}
                                            placeholder="Add context for the verifier"
                                        />
                                    </label>
                                    <button type="submit" className="secondary-btn">Queue review item</button>
                                </form>
                            ) : null}
                        </div>
                    </section>
                ) : null}

                {roleView.showMeasurementLog ? (
                    <section className="panel">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Measurements</p>
                                <h3>Recent field evidence</h3>
                                <p className="panel-subtitle">
                                    Showing {filteredMeasurementRecords.length} of {measurementRecords.length} measurements
                                </p>
                            </div>
                        </div>

                        <div className="measurement-health">
                            <article className="measurement-health-card">
                                <span>Recent capture pulse</span>
                                <strong>{measurementTrend.reduce((sum, day) => sum + day.count, 0)} records</strong>
                                <div className="measurement-trend" aria-label="Measurement capture trend">
                                    {measurementTrend.map((day) => (
                                        <article className="measurement-trend-bar" key={day.label}>
                                            <span>{day.label}</span>
                                            <div className="measurement-trend-track">
                                                <div
                                                    className="measurement-trend-fill"
                                                    style={{ height: `${Math.max(day.count * 20, 12)}px` }}
                                                />
                                            </div>
                                            <strong>{day.count}</strong>

                                            <div className="measurement-health">
                                                <article className="measurement-health-card">
                                                    <span>Recent capture pulse</span>
                                                    <strong>{measurementTrend.reduce((sum, day) => sum + day.count, 0)} records</strong>
                                                    <div className="measurement-trend" aria-label="Measurement capture trend">
                                                        {measurementTrend.map((day) => (
                                                            <article className="measurement-trend-bar" key={day.label}>
                                                                <span>{day.label}</span>
                                                                <div className="measurement-trend-track">
                                                                    <div
                                                                        className="measurement-trend-fill"
                                                                        style={{ height: `${Math.max(day.count * 20, 12)}px` }}
                                                                    />
                                                                </div>
                                                                <strong>{day.count}</strong>
                                                            </article>
                                                        ))}
                                                    </div>
                                                </article>

                                                <article className="measurement-health-card">
                                                    <span>Newest evidence</span>
                                                    <strong>{latestMeasurement ? measurementFreshness(latestMeasurement.capturedAt) : 'No records yet'}</strong>
                                                    <p>Latest value in the log</p>
                                                    <button
                                                        type="button"
                                                        className="ghost-btn measurement-review-btn"
                                                        onClick={handleReviewLatestMeasurement}
                                                        disabled={!latestMeasurement || reviewedMeasurementIds.includes(latestMeasurement.id)}
                                                    >
                                                        {latestMeasurement && reviewedMeasurementIds.includes(latestMeasurement.id)
                                                            ? 'Latest reviewed'
                                                            : 'Mark latest reviewed'}
                                                    </button>
                                                    <span className="measurement-review-count">
                                                        {reviewedMeasurementCount} reviewed, {measurementRecords.length - reviewedMeasurementCount} pending
                                                    </span>
                                                </article>
                                            </div>
                                        </article>
                                    ))}
                                </div>
                            </article>
                            <article className="measurement-health-card">
                                <span>Newest evidence</span>
                                <strong>{measurementRecords[0] ? measurementFreshness(measurementRecords[0].capturedAt) : 'No records yet'}</strong>
                                <p>Latest value in the log</p>
                            </article>
                        </div>

                        <div className="panel-tools">
                            <label className="tool-field">
                                Search measurements
                                <input
                                    value={measurementQuery}
                                    onChange={(event) => setMeasurementQuery(event.target.value)}
                                    placeholder="Search by farm, metric, value, or source"
                                />
                            </label>
                        </div>

                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Farm</th>
                                        <th>Metric</th>
                                        <th>Value</th>
                                        <th>Source</th>
                                        <th>Date</th>
                                        <th>Freshness</th>
                                        <th>Review</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredMeasurementRecords.map((measurement) => (
                                        <tr key={measurement.id}>
                                            <td>{farmRecords.find((farm) => farm.id === measurement.farmId)?.name}</td>
                                            <td>{measurement.metric}</td>
                                            <td>{measurement.value}</td>
                                            <td>{measurement.source}</td>
                                            <td>{measurement.capturedAt}</td>
                                            <td><span className="measurement-age">{measurementFreshness(measurement.capturedAt)}</span></td>
                                            <td>
                                                <span className={`measurement-review-pill ${reviewedMeasurementIds.includes(measurement.id) ? 'reviewed' : 'pending'}`}>
                                                    {reviewedMeasurementIds.includes(measurement.id) ? 'Reviewed' : 'Pending'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {filteredMeasurementRecords.length === 0 ? (
                            <div className="empty-search" style={{ marginTop: '16px' }}>
                                No measurements match the current search.
                            </div>
                        ) : null}
                    </section>
                ) : null}

                {roleView.showVerificationForm ? (
                    <section className="panel">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Verification</p>
                                <h3>Evidence checklist and approval state</h3>
                            </div>
                            <span className="panel-note">Third-party review ready</span>
                        </div>

                        <div className="verification-health">
                            <article className="verification-health-card">
                                <span>Completion</span>
                                <strong>{verificationCompletionRatio}%</strong>
                                <div className="progress-meter verification-health-meter" aria-label="Verification completion">
                                    <div className="progress-meter-bar" style={{ width: `${verificationCompletionRatio}%` }} />
                                </div>
                            </article>
                            <article className="verification-health-card">
                                <span>Complete items</span>
                                <strong>{verificationStatusCounts.complete}</strong>
                                <p>Ready for signoff</p>
                            </article>
                            <article className="verification-health-card">
                                <span>Pending items</span>
                                <strong>{verificationStatusCounts.pending}</strong>
                                <p>Still waiting in queue</p>
                            </article>
                        </div>

                        <div className="verification-list">
                            {verificationRecords.map((item) => (
                                <article className="verification-item" key={item.label}>
                                    <div className={`verification-mark ${item.status}`}>
                                        {item.status === 'complete' ? 'Complete' : 'Pending'}
                                    </div>
                                    <div>
                                        <h4>{item.label}</h4>
                                        <p>{item.note}</p>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {roleView.showVerificationForm ? (
                    <section className="panel panel-large">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Verification roadmap</p>
                                <h3>How the current review queue is moving</h3>
                            </div>
                            <span className="panel-note">{verificationRoadmap.filter((item) => item.status === 'complete').length} ready</span>
                        </div>

                        <div className="verification-roadmap">
                            {verificationRoadmap.map((item) => (
                                <article className={`verification-roadmap-card ${item.status}`} key={`${item.label}-${item.stepNumber}`}>
                                    <div className="verification-roadmap-header">
                                        <div>
                                            <span>Step {item.stepNumber}</span>
                                            <strong>{item.reviewLabel}</strong>
                                        </div>
                                        <span className={`verification-mark ${item.status}`}>
                                            {item.status === 'complete' ? 'Complete' : 'Pending'}
                                        </span>
                                    </div>

                                    <h4>{item.label}</h4>
                                    <p>{item.note}</p>
                                    <div className="verification-roadmap-footer">
                                        <span>{item.reviewDateLabel}</span>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {roleView.showVerificationForm ? (
                    <section className="panel">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Verification inputs</p>
                                <h3>Data the independent reviewer will expect</h3>
                            </div>
                        </div>

                        <div className="checklist-grid">
                            {verificationDataRequired.map((item) => (
                                <article className="checklist-card" key={item.label}>
                                    <h4>{item.label}</h4>
                                    <p>{item.note}</p>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {roleView.showFarmForms ? (
                    <section className="panel">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Farm gadgets</p>
                                <h3>Recommended field devices without phones or laptops</h3>
                            </div>
                        </div>

                        <div className="checklist-grid">
                            {farmDevices.map((item) => (
                                <article className="checklist-card" key={item.label}>
                                    <h4>{item.label}</h4>
                                    <p>{item.note}</p>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {roleView.showCompliance ? (
                    <section className="panel panel-large">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Compliance</p>
                                <h3>Standards the solution should align to</h3>
                            </div>
                        </div>

                        <div className="highlight-grid compliance-grid">
                            {complianceStandards.map((item) => (
                                <article className={`highlight-card tone-${toneTone[item.tone]}`} key={item.title}>
                                    <h4>{item.title}</h4>
                                    <p>{item.description}</p>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {roleView.showActivityTrail ? (
                    <section className="panel panel-large">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">Activity trail</p>
                                <h3>Recent actions across the MRV workflow</h3>
                            </div>
                            <span className="panel-note">{activityLog.length} actions tracked</span>
                        </div>

                        <div className="activity-feed-header">
                            <div>
                                <span>Workflow pulse</span>
                                <strong>{latestActivity ? latestActivity.action : 'Waiting for activity'}</strong>
                            </div>
                            <p>{latestActivity ? new Date(latestActivity.timestamp).toLocaleDateString() : 'Nothing has been logged yet.'}</p>
                        </div>

                        <div className="activity-trend" aria-label="Recent activity trend">
                            {activityTrend.map((day) => (
                                <article className="activity-trend-bar" key={day.label}>
                                    <span>{day.label}</span>
                                    <div className="activity-trend-track">
                                        <div
                                            className="activity-trend-fill"
                                            style={{ height: `${Math.max(day.count * 24, 14)}px` }}
                                        />
                                    </div>
                                    <strong>{day.count}</strong>
                                </article>
                            ))}
                        </div>

                        {latestActivity ? (
                            <div className="activity-summary">
                                <span>Latest action</span>
                                <strong>{latestActivity.action}</strong>
                                <p>{latestActivity.detail}</p>
                            </div>
                        ) : null}

                        <div className="activity-list">
                            {activityLog.length > 0 ? activityLog.map((entry) => (
                                <article className="activity-card" key={entry.id}>
                                    <span className="activity-rail-dot" aria-hidden="true" />
                                    <div>
                                        <h4>{entry.action}</h4>
                                        <p>{entry.detail}</p>
                                    </div>
                                    <time dateTime={entry.timestamp}>
                                        {new Date(entry.timestamp).toLocaleString()}
                                    </time>
                                </article>
                            )) : (
                                <div className="empty-state">
                                    <h4>No activity yet</h4>
                                    <p>Actions taken in this session will appear here and in the downloaded bundle.</p>
                                </div>
                            )}
                        </div>
                    </section>
                ) : null}

                {roleView.showTokenLedger ? (
                    <section className="panel panel-large">
                        <div className="panel-heading">
                            <div>
                                <p className="section-label">ACT token ledger</p>
                                <h3>Credits prepared for minting or listing</h3>
                            </div>
                            <span className="panel-note">{mintedTokens} minted batches</span>
                        </div>

                        <div className="token-list">
                            {tokenRecords.map((batch) => (
                                <article className="token-card" key={batch.tokenId}>
                                    <div>
                                        <p>{batch.farm}</p>
                                        <h4>{batch.credits}</h4>
                                    </div>
                                    <div className="token-meta">
                                        <span>{batch.tokenId}</span>
                                        <strong>{batch.state}</strong>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}
            </main>
        </div>
    );
}

export default App;
