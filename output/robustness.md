# Robustness check

**Does the top 5 hold? Yes.** The same five shows (TBPN, Conversations with Tyler, No Priors, How I Write, EconTalk) are the top 5 by P4P in 7 of 7 variants (the base run plus the four the README asks for, plus two extras: how unmeasured guests enter the percentiles, and TBPN without its size adjustment). The order within the five shifts; the fit stays positive and significant in every variant.

Each variant re-runs the whole pipeline (Guest Weight → top-N mean → fit → P4P) with one setting changed.

| Variant | Fit slope | R² | p | Top 5 by P4P | Same top 5? | Spearman vs base |
|---|---|---|---|---|---|---|
| Base: top 50, fame/stature 50/50 | 12.8 | 0.42 | 0.003 | TBPN, Conversations with Tyler, No Priors, How I Write, EconTalk | same order | 1.00 |
| Top 25 | 9.0 | 0.38 | 0.005 | No Priors, Conversations with Tyler, TBPN, How I Write, EconTalk | same five | 0.94 |
| Top 75 | 13.8 | 0.39 | 0.004 | TBPN, Conversations with Tyler, How I Write, No Priors, EconTalk | same five | 0.96 |
| Fame/stature 35/65 | 12.3 | 0.38 | 0.005 | Conversations with Tyler, TBPN, No Priors, EconTalk, How I Write | same five | 0.99 |
| Fame/stature 65/35 | 13.3 | 0.45 | 0.002 | TBPN, How I Write, No Priors, Conversations with Tyler, EconTalk | same five | 0.99 |
| Percentiles across all guests (unmeasured ranked lowest) | 10.3 | 0.35 | 0.007 | No Priors, Conversations with Tyler, EconTalk, TBPN, How I Write | same five | 0.98 |
| TBPN at raw Spotify count | 12.7 | 0.42 | 0.003 | TBPN, Conversations with Tyler, No Priors, How I Write, EconTalk | same order | 1.00 |

## P4P rank of every show under each variant

| Show | Base | Top 25 | Top 75 | Fame/stature 35/65 | Fame/stature 65/35 | All-guest pct | TBPN raw |
|---|---|---|---|---|---|---|---|
| TBPN | 1 | 3 | 1 | 2 | 1 | 4 | 1 |
| Conversations with Tyler | 2 | 2 | 2 | 1 | 4 | 2 | 2 |
| No Priors | 3 | 1 | 4 | 3 | 3 | 1 | 3 |
| How I Write | 4 | 4 | 3 | 5 | 2 | 5 | 4 |
| EconTalk | 5 | 5 | 5 | 4 | 5 | 3 | 5 |
| Invest Like the Best | 6 | 6 | 6 | 6 | 7 | 7 | 6 |
| Sourcery | 7 | 7 | 8 | 7 | 6 | 6 | 7 |
| The Tim Ferriss Show | 8 | 9 | 7 | 8 | 8 | 8 | 8 |
| The Knowledge Project | 9 | 15 | 9 | 10 | 9 | 10 | 9 |
| All-In | 10 | 11 | 11 | 9 | 10 | 11 | 10 |
| Uncapped with Jack Altman | 11 | 8 | 14 | 11 | 11 | 9 | 11 |
| Lex Fridman Podcast | 12 | 13 | 13 | 12 | 12 | 13 | 12 |
| Dwarkesh Podcast | 13 | 12 | 16 | 13 | 13 | 12 | 13 |
| David Senra | 14 | 10 | 10 | 14 | 15 | 14 | 14 |
| Cheeky Pint | 15 | 14 | 12 | 15 | 16 | 15 | 15 |
| My First Million | 16 | 16 | 15 | 16 | 14 | 16 | 16 |
| Lenny's Podcast | 17 | 17 | 17 | 17 | 17 | 17 | 17 |
| Jack Neel Podcast | 18 | 18 | 18 | 18 | 18 | 18 | 18 |
| Relentless | 19 | 19 | 19 | 19 | 19 | 19 | 19 |

## P4P multiple under each variant

| Show | Base | Top 25 | Top 75 | Fame/stature 35/65 | Fame/stature 65/35 | All-guest pct | TBPN raw |
|---|---|---|---|---|---|---|---|
| TBPN | 14.55× | 9.75× | 18.06× | 15.43× | 14.95× | 14.02× | 16.88× |
| Conversations with Tyler | 12.90× | 13.20× | 13.58× | 17.74× | 10.08× | 15.17× | 13.04× |
| No Priors | 12.44× | 16.76× | 8.24× | 14.97× | 10.13× | 19.12× | 12.41× |
| How I Write | 10.73× | 6.53× | 12.16× | 8.15× | 13.16× | 8.71× | 10.71× |
| EconTalk | 6.78× | 4.90× | 7.43× | 14.25× | 4.63× | 14.67× | 6.81× |
| Invest Like the Best | 4.63× | 3.16× | 4.75× | 5.41× | 4.13× | 5.39× | 4.65× |
| Sourcery | 3.65× | 2.84× | 2.09× | 3.30× | 4.22× | 5.81× | 3.59× |
| The Tim Ferriss Show | 3.06× | 2.34× | 4.29× | 3.08× | 2.90× | 2.39× | 3.11× |
| The Knowledge Project | 1.21× | 0.71× | 1.40× | 1.07× | 1.44× | 1.14× | 1.21× |
| All-In | 1.18× | 1.42× | 1.16× | 1.26× | 1.02× | 0.96× | 1.20× |
| Uncapped with Jack Altman | 0.85× | 2.48× | 0.69× | 1.02× | 0.67× | 1.75× | 0.83× |
| Lex Fridman Podcast | 0.70× | 1.33× | 0.73× | 0.89× | 0.54× | 0.63× | 0.71× |
| Dwarkesh Podcast | 0.49× | 1.38× | 0.20× | 0.51× | 0.45× | 0.71× | 0.48× |
| David Senra | 0.45× | 2.15× | 1.29× | 0.51× | 0.36× | 0.41× | 0.44× |
| Cheeky Pint | 0.36× | 0.86× | 1.15× | 0.44× | 0.27× | 0.28× | 0.35× |
| My First Million | 0.27× | 0.12× | 0.31× | 0.17× | 0.40× | 0.21× | 0.27× |
| Lenny's Podcast | 0.07× | 0.05× | 0.06× | 0.07× | 0.09× | 0.13× | 0.07× |
| Jack Neel Podcast | 0.02× | 0.01× | 0.01× | 0.01× | 0.07× | 0.01× | 0.02× |
| Relentless | 0.00× | 0.00× | 0.01× | 0.00× | 0.00× | 0.00× | 0.00× |

## Notes

- Shows with fewer guests than N use all of them: David Senra (45) and Cheeky Pint (36) at N = 50; also Uncapped (61) at N = 75. At N = 25 those small shows are compared on their best guests only, which is why David Senra and Cheeky Pint rise there.
- Multiples move more than ranks: the fit's slope changes between variants and P4P is exponential in the gap to the line, so read the multiples as rough ("about 10×", not "10.3×").
- Fit quality is on the base run: R² is moderate (about 0.4 with 19 shows). Bigger shows do book bigger guests, but show size explains less than half the variation in guest scores, which is what makes the P4P comparison interesting.
- **Guest volume matters.** A fixed top 50 is more selective for a show with many guests: the top 50 of TBPN's 1,381 guests are its best 4%, while for Uncapped's 61 guests they are 82%. Across shows, the gap to the fitted line correlates with the number of guests (Spearman 0.51, p = 0.02). If the cut is proportional instead (each show's top 20% of guests, or all its guests), the size fit collapses (R² 0.07 and 0.06, not significant), so the README's rule would stop publication. The P4P result therefore rewards booking many strong guests, not just a high hit rate. Small, selective shows (David Senra, Cheeky Pint, Uncapped) have the highest averages but too few guests to fill a top 50.

## TBPN's size adjustment

TBPN's Spotify count (651) is scaled by 1.15 to 749, from its YouTube subscribers per Spotify rating relative to the other shows (`data/size_adjustments.csv`, `data/audience_check.csv`). Its X show account suggests a much bigger off-Spotify audience, so here is how the result moves with larger multipliers:

| TBPN multiplier | TBPN size | TBPN rank | TBPN P4P | Top 5 |
|---|---|---|---|---|
| 1× | 651 | 1 | 16.9× | TBPN, Conversations with Tyler, No Priors, How I Write, EconTalk |
| 1.15× | 749 | 1 | 14.6× | TBPN, Conversations with Tyler, No Priors, How I Write, EconTalk |
| 1.5× | 976 | 3 | 11.0× | Conversations with Tyler, No Priors, TBPN, How I Write, EconTalk |
| 2× | 1,302 | 4 | 8.2× | No Priors, Conversations with Tyler, How I Write, TBPN, EconTalk |
| 3× | 1,953 | 5 | 5.5× | No Priors, Conversations with Tyler, How I Write, EconTalk, TBPN |
| 5× | 3,255 | 7 | 3.3× | No Priors, Conversations with Tyler, How I Write, EconTalk, Invest Like the Best |

TBPN stays #1 up to about 1.3×. Beyond that it slips to #3 (1.5×) or out of the top 5 (5×), while the other four leaders hold their places.
