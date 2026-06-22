import type { ChecklistEntry, Farm, HighlightCard, Measurement, TokenBatch, VerificationItem } from './types';

export const farms: Farm[] = [
    {
        id: 'farm-001',
        name: 'Ajowi North Agroforestry Block',
        owner: 'Mary Akinyi',
        location: 'Kisumu County, Kenya',
        hectares: 12.4,
        treesPlanted: 1840,
        species: ['Grevillea', 'Mango', 'Sesbania'],
        status: 'verified',
        coordinates: '-0.0910, 34.7679',
        soilCarbonChange: '+0.42 tC/ha',
        lastUpdated: '2 hours ago',
    },
    {
        id: 'farm-002',
        name: 'Ajowi River Basin Plot',
        owner: 'Joseph Otieno',
        location: 'Siaya County, Kenya',
        hectares: 8.9,
        treesPlanted: 1115,
        species: ['Calliandra', 'Avocado', 'Gliricidia'],
        status: 'monitoring',
        coordinates: '-0.0586, 34.2840',
        soilCarbonChange: '+0.27 tC/ha',
        lastUpdated: 'Today',
    },
    {
        id: 'farm-003',
        name: 'Ajowi Upland Pilot',
        owner: 'Grace Auma',
        location: 'Homa Bay County, Kenya',
        hectares: 15.7,
        treesPlanted: 2096,
        species: ['Moringa', 'Albizia', 'Papaya'],
        status: 'baseline',
        coordinates: '-0.5273, 34.4571',
        soilCarbonChange: 'Baseline only',
        lastUpdated: 'Yesterday',
    },
];

export const measurements: Measurement[] = [
    {
        id: 'm-001',
        farmId: 'farm-001',
        metric: 'DBH average',
        value: '18.2 cm',
        source: 'Field crew + DBH tape',
        capturedAt: '2026-06-20',
    },
    {
        id: 'm-002',
        farmId: 'farm-001',
        metric: 'Tree height average',
        value: '6.4 m',
        source: 'Field estimator',
        capturedAt: '2026-06-20',
    },
    {
        id: 'm-003',
        farmId: 'farm-002',
        metric: 'Soil organic carbon',
        value: '2.14%',
        source: 'Lab sample',
        capturedAt: '2026-06-19',
    },
    {
        id: 'm-004',
        farmId: 'farm-002',
        metric: 'Rainfall',
        value: '18.7 mm',
        source: 'Digital gauge',
        capturedAt: '2026-06-21',
    },
    {
        id: 'm-005',
        farmId: 'farm-003',
        metric: 'Boundary GPS points',
        value: '14 points',
        source: 'GPS tracker',
        capturedAt: '2026-06-18',
    },
];

export const verificationItems: VerificationItem[] = [
    {
        label: 'Farm boundary polygon captured',
        status: 'complete',
        note: 'GPS coordinates and geo-tagged evidence uploaded',
    },
    {
        label: 'Tree inventory cross-checked',
        status: 'complete',
        note: 'Counts validated against field sheets',
    },
    {
        label: 'Soil carbon baseline completed',
        status: 'pending',
        note: 'Waiting on lab certificate for Plot 3',
    },
    {
        label: 'Independent verifier review',
        status: 'pending',
        note: 'Audit queue opened for third-party approval',
    },
];

export const tokenBatches: TokenBatch[] = [
    {
        farm: 'Ajowi North Agroforestry Block',
        credits: '126.4 tCO2e',
        tokenId: 'ACT-2026-00018',
        state: 'Minted',
    },
    {
        farm: 'Ajowi River Basin Plot',
        credits: '91.8 tCO2e',
        tokenId: 'ACT-2026-00019',
        state: 'Pending mint',
    },
    {
        farm: 'Ajowi Upland Pilot',
        credits: '118.2 tCO2e',
        tokenId: 'ACT-2026-00020',
        state: 'Listed',
    },
];

export const projectObjectives: HighlightCard[] = [
    {
        title: 'Increase tree cover',
        description: 'Support agroforestry on farmland to improve canopy cover and biodiversity.',
        tone: 'leaf',
    },
    {
        title: 'Store atmospheric carbon',
        description: 'Measure biomass and soil changes that represent additional carbon sequestration.',
        tone: 'earth',
    },
    {
        title: 'Create farmer income',
        description: 'Turn verified carbon volume into a marketable income stream for smallholders.',
        tone: 'sun',
    },
    {
        title: 'Keep evidence auditable',
        description: 'Preserve verifiable field data, sensor records, and calibration history.',
        tone: 'sky',
    },
];

export const verificationDataRequired: ChecklistEntry[] = [
    {
        label: 'GPS coordinates of each farm',
        note: 'Needed to define the project boundary and geo-tag evidence.',
    },
    {
        label: 'Tree inventory and species list',
        note: 'Supports biomass estimation and species-level reporting.',
    },
    {
        label: 'Soil carbon baseline and remeasurement',
        note: 'Used to compare before-and-after soil organic carbon levels.',
    },
    {
        label: 'Land-use history and farmer records',
        note: 'Confirms eligibility and traceability for the project area.',
    },
    {
        label: 'Calibration data and calculation model',
        note: 'Ensures the carbon estimate can be reproduced by a verifier.',
    },
];

export const farmDevices: ChecklistEntry[] = [
    {
        label: 'Soil moisture and pH sensors',
        note: 'Measures soil conditions that can influence carbon storage.',
    },
    {
        label: 'DBH tape and tree height tools',
        note: 'Captures biomass input data from field teams.',
    },
    {
        label: 'Digital rain gauge and weather station',
        note: 'Records rainfall, temperature, and wind conditions on-site.',
    },
    {
        label: 'Solar data logger and GPS tracker',
        note: 'Keeps the system running off-grid while preserving location data.',
    },
    {
        label: 'Carbon flux sensor',
        note: 'Supports ongoing atmospheric exchange measurements where available.',
    },
];

export const complianceStandards: HighlightCard[] = [
    {
        title: 'Verra VCS',
        description: 'Primary carbon accounting and verification standard for the project.',
        tone: 'leaf',
    },
    {
        title: 'Gold Standard',
        description: 'Climate-credit framework for high-integrity project claims.',
        tone: 'sun',
    },
    {
        title: 'IPCC guidance',
        description: 'Reference methodology for carbon estimation and reporting.',
        tone: 'sky',
    },
    {
        title: 'UN SDGs',
        description: 'Mapped to goals 1, 8, 13, and 15 for social and environmental impact.',
        tone: 'earth',
    },
];
