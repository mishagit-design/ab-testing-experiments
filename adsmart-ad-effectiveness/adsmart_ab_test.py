# ============================================================
# AdSmart A/B Test Analysis
# Author: Misha Laleh
# Description: Statistical analysis of ad exposure effectiveness
# using hypothesis testing, conversion rate analysis, and
# segment-level breakdowns to inform campaign decisions.
# ============================================================

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. LOAD & INSPECT DATA
# ============================================================

df = pd.read_csv('adsmartABdata.csv')

print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)
print(f"Total records: {len(df):,}")
print(f"Columns: {list(df.columns)}")
print(f"\nExperiment group distribution:")
print(df['experiment'].value_counts())
print(f"\nNull values:\n{df.isnull().sum()}")


# ============================================================
# 2. FEATURE ENGINEERING
# ============================================================

# Create a single conversion column
# 'yes' = user recalled/clicked the ad (positive signal)
# 'no'  = user actively rejected (negative signal)
# Neither = no response recorded
df['converted'] = df['yes'].apply(lambda x: 1 if x == 1 else 0)
df['rejected'] = df['no'].apply(lambda x: 1 if x == 1 else 0)
df['no_response'] = ((df['yes'] == 0) & (df['no'] == 0)).astype(int)

print("\n" + "=" * 60)
print("RESPONSE DISTRIBUTION")
print("=" * 60)
print(f"Converted (yes=1):   {df['converted'].sum():,} ({df['converted'].mean()*100:.1f}%)")
print(f"Rejected  (no=1):    {df['rejected'].sum():,} ({df['rejected'].mean()*100:.1f}%)")
print(f"No response:         {df['no_response'].sum():,} ({df['no_response'].mean()*100:.1f}%)")


# ============================================================
# 3. CONVERSION RATES BY GROUP
# ============================================================

print("\n" + "=" * 60)
print("CONVERSION RATES BY EXPERIMENT GROUP")
print("=" * 60)

group_summary = df.groupby('experiment').agg(
    total_users=('converted', 'count'),
    conversions=('converted', 'sum'),
    conversion_rate=('converted', 'mean'),
    rejections=('rejected', 'sum'),
    rejection_rate=('rejected', 'mean')
).reset_index()

group_summary['conversion_rate_pct'] = group_summary['conversion_rate'] * 100
group_summary['rejection_rate_pct'] = group_summary['rejection_rate'] * 100

print(group_summary[['experiment', 'total_users', 'conversions',
                       'conversion_rate_pct', 'rejections', 'rejection_rate_pct']].to_string(index=False))

# Lift calculation
control_rate = group_summary.loc[group_summary['experiment'] == 'control', 'conversion_rate'].values[0]
exposed_rate = group_summary.loc[group_summary['experiment'] == 'exposed', 'conversion_rate'].values[0]
lift = ((exposed_rate - control_rate) / control_rate) * 100

print(f"\nAbsolute lift: {(exposed_rate - control_rate)*100:.2f} percentage points")
print(f"Relative lift: {lift:.1f}%")


# ============================================================
# 4. HYPOTHESIS TEST — CHI-SQUARE TEST
# ============================================================
# H0: There is no difference in conversion rate between
#     control and exposed groups
# H1: The exposed group has a significantly different
#     conversion rate than the control group
# Significance level: alpha = 0.05

print("\n" + "=" * 60)
print("HYPOTHESIS TEST — CHI-SQUARE")
print("=" * 60)
print("H0: No difference in conversion rate between groups")
print("H1: Exposed group has a different conversion rate")
print("Alpha: 0.05")

control = df[df['experiment'] == 'control']
exposed = df[df['experiment'] == 'exposed']

contingency_table = np.array([
    [control['converted'].sum(), len(control) - control['converted'].sum()],
    [exposed['converted'].sum(), len(exposed) - exposed['converted'].sum()]
])

print(f"\nContingency Table:")
print(f"             Converted   Not Converted")
print(f"Control:     {contingency_table[0][0]:>9,}   {contingency_table[0][1]:>13,}")
print(f"Exposed:     {contingency_table[1][0]:>9,}   {contingency_table[1][1]:>13,}")

chi2, p_value, dof, expected = chi2_contingency(contingency_table)

print(f"\nChi-square statistic: {chi2:.4f}")
print(f"P-value:              {p_value:.4f}")
print(f"Degrees of freedom:   {dof}")

if p_value < 0.05:
    print(f"\nResult: STATISTICALLY SIGNIFICANT (p={p_value:.4f} < 0.05)")
    print("We reject H0. The ad exposure had a significant effect on conversion.")
else:
    print(f"\nResult: NOT STATISTICALLY SIGNIFICANT (p={p_value:.4f} >= 0.05)")
    print("We fail to reject H0. No significant difference detected.")


# ============================================================
# 5. SEGMENT ANALYSIS — DEVICE
# ============================================================

print("\n" + "=" * 60)
print("SEGMENT ANALYSIS — TOP DEVICES")
print("=" * 60)

top_devices = df['device_make'].value_counts().head(5).index
device_df = df[df['device_make'].isin(top_devices)]

device_summary = device_df.groupby(['device_make', 'experiment']).agg(
    users=('converted', 'count'),
    conversion_rate=('converted', 'mean')
).reset_index()

device_pivot = device_summary.pivot(index='device_make', columns='experiment', values='conversion_rate') * 100
device_pivot['lift_pct_pts'] = device_pivot['exposed'] - device_pivot['control']
print(device_pivot.round(2))


# ============================================================
# 6. SEGMENT ANALYSIS — BROWSER
# ============================================================

print("\n" + "=" * 60)
print("SEGMENT ANALYSIS — BROWSER")
print("=" * 60)

browser_summary = df.groupby(['browser', 'experiment']).agg(
    users=('converted', 'count'),
    conversion_rate=('converted', 'mean')
).reset_index()

browser_pivot = browser_summary.pivot(index='browser', columns='experiment', values='conversion_rate') * 100
browser_pivot['lift_pct_pts'] = browser_pivot['exposed'] - browser_pivot['control']
print(browser_pivot.round(2))


# ============================================================
# 7. HOURLY CONVERSION PATTERN
# ============================================================

print("\n" + "=" * 60)
print("CONVERSION RATE BY HOUR")
print("=" * 60)

hourly = df.groupby(['hour', 'experiment'])['converted'].mean().unstack() * 100
print(hourly.round(2))


# ============================================================
# 8. VISUALIZATIONS
# ============================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('AdSmart A/B Test Analysis', fontsize=16, fontweight='bold')

# Plot 1: Conversion rate by group
ax1 = axes[0, 0]
colors = ['#4C72B0', '#DD8452']
bars = ax1.bar(group_summary['experiment'], group_summary['conversion_rate_pct'], color=colors)
ax1.set_title('Conversion Rate by Group', fontweight='bold')
ax1.set_ylabel('Conversion Rate (%)')
ax1.set_xlabel('Experiment Group')
for bar, val in zip(bars, group_summary['conversion_rate_pct']):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
             f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')

# Plot 2: Conversion rate by device
ax2 = axes[0, 1]
device_pivot[['control', 'exposed']].plot(kind='bar', ax=ax2, color=colors)
ax2.set_title('Conversion Rate by Device (Top 5)', fontweight='bold')
ax2.set_ylabel('Conversion Rate (%)')
ax2.set_xlabel('Device')
ax2.legend(['Control', 'Exposed'])
ax2.tick_params(axis='x', rotation=30)

# Plot 3: Conversion rate by browser
ax3 = axes[1, 0]
browser_pivot[['control', 'exposed']].plot(kind='bar', ax=ax3, color=colors)
ax3.set_title('Conversion Rate by Browser', fontweight='bold')
ax3.set_ylabel('Conversion Rate (%)')
ax3.set_xlabel('Browser')
ax3.legend(['Control', 'Exposed'])
ax3.tick_params(axis='x', rotation=30)

# Plot 4: Hourly conversion pattern
ax4 = axes[1, 1]
hourly.plot(ax=ax4, marker='o', color=colors)
ax4.set_title('Conversion Rate by Hour of Day', fontweight='bold')
ax4.set_ylabel('Conversion Rate (%)')
ax4.set_xlabel('Hour')
ax4.legend(['Control', 'Exposed'])

plt.tight_layout()
plt.savefig('adsmart_ab_results.png', dpi=150, bbox_inches='tight')
plt.show()
print("\nVisualization saved as 'adsmart_ab_results.png'")


# ============================================================
# 9. BUSINESS RECOMMENDATION
# ============================================================

print("\n" + "=" * 60)
print("BUSINESS RECOMMENDATION")
print("=" * 60)
print(f"""
The A/B test compared ad recall and engagement between users
exposed to the AdSmart campaign versus a control group.

Key Findings:
  - Control conversion rate:  {control_rate*100:.2f}%
  - Exposed conversion rate:  {exposed_rate*100:.2f}%
  - Relative lift:            {lift:.1f}%
  - Statistical significance: {'Yes' if p_value < 0.05 else 'No'} (p={p_value:.4f})

{'The campaign drove a statistically significant lift in conversion.' if p_value < 0.05 else 'The campaign did not drive a statistically significant lift.'}

Segment insights should be used to prioritize ad spend toward
devices and browsers showing the highest incremental lift,
and to identify hours of day where the exposed group outperforms
control most significantly.
""")
