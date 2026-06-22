export type FarmStatus = 'baseline' | 'monitoring' | 'verified';

export interface Farm {
    id: string;
    name: string;
    owner: string;
    location: string;
    hectares: number;
    treesPlanted: number;
    species: string[];
    status: FarmStatus;
    coordinates: string;
    soilCarbonChange: string;
    lastUpdated: string;
}

export interface Measurement {
    id: string;
    farmId: string;
    metric: string;
    value: string;
    source: string;
    capturedAt: string;
}

export interface VerificationItem {
    label: string;
    status: 'complete' | 'pending';
    note: string;
}

export interface TokenBatch {
    farm: string;
    credits: string;
    tokenId: string;
    state: 'Pending mint' | 'Minted' | 'Listed';
}

export interface HighlightCard {
    title: string;
    description: string;
    tone: 'leaf' | 'earth' | 'sun' | 'sky';
}

export interface ChecklistEntry {
    label: string;
    note: string;
}
