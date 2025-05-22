# accounts/dataset_utils.py
from collections import defaultdict
from .models import ProfileScan

def process_dataset_statistics(scans):
    """Process dataset scans and prepare visualization data"""
    total_accounts = len(scans)
    fake_accounts = sum(1 for scan in scans if scan.risk_score >= 70)
    real_accounts = total_accounts - fake_accounts
    avg_risk_score = round(sum(scan.risk_score for scan in scans) / total_accounts, 1)

    # Prepare data for charts
    account_data = {
        'real': real_accounts,
        'fake': fake_accounts
    }

    # Group risk scores into ranges for the bar chart
    risk_ranges = defaultdict(int)
    for scan in scans:
        range_key = (scan.risk_score // 10) * 10
        risk_ranges[range_key] += 1

    risk_score_data = {
        'labels': [f'{i}-{i+9}' for i in range(0, 100, 10)],
        'values': [risk_ranges[i] for i in range(0, 100, 10)]
    }

    return {
        'total_accounts': total_accounts,
        'real_accounts': real_accounts,
        'fake_accounts': fake_accounts,
        'avg_risk_score': avg_risk_score,
        'account_data': account_data,
        'risk_score_data': risk_score_data
    }