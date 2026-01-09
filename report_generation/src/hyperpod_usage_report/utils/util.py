import pandas as pd


def has_mig_usage(df: pd.DataFrame, is_detailed: bool) -> bool:
    """Check if any MIG resources are used in the report"""
    if df.empty:
        return False
    
    if is_detailed:
        mig_cols = ['utilized_mig_hours', 'utilized_mig_count']
    else:  # summary
        mig_cols = ['total_mig_utilization_hours', 'allocated_mig_utilization_hours', 'borrowed_mig_utilization_hours']
    
    # Check if any MIG column has non-zero/non-null values
    for col in mig_cols:
        if col in df.columns and df[col].notna().any() and (df[col] > 0).any():
            return True
    
    # Check if mig_profile column has any non-null values
    if 'mig_profile' in df.columns and df['mig_profile'].notna().any():
        return True
    
    return False


def filter_zero_usage_rows(df: pd.DataFrame, is_detailed: bool) -> pd.DataFrame:
    """Filter out rows with all zero usage values"""
    if df.empty:
        return df
    
    if is_detailed:
        usage_cols = ['utilized_neuron_core_hours', 'utilized_gpu_hours', 'utilized_vcpu_hours', 'utilized_mig_hours']
    else:  # summary
        usage_cols = ['total_neuron_core_utilization_hours', 'total_gpu_utilization_hours', 'total_vcpu_utilization_hours', 'total_mig_utilization_hours']
    
    # Only check columns that exist in the dataframe
    existing_cols = [col for col in usage_cols if col in df.columns]
    
    if not existing_cols:
        return df
    
    # Keep rows where at least one usage column has a value > 0
    mask = (df[existing_cols].fillna(0) > 0).any(axis=1)
    return df[mask]