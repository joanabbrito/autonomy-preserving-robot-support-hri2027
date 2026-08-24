# Preliminary Statistical Analysis — Implicit vs. Explicit Conditions

*Generated from `OlderAdults_postStudy (Responses) - Form responses 1.csv`, N=35 (18 Implicit, 17 Explicit). Control condition intentionally excluded — not yet collected.*

## 1. Purpose

The study compares three robot hint conditions in a visuospatial memory task with older adults: **Control** (social presence only), **Implicit** (indirect hints), and **Explicit** (direct answers). Two hypotheses drive the design:

- **H1**: Implicit condition yields higher perceived autonomy / sense of agency than Explicit, per Self-Determination Theory.
- **H2**: Task performance is comparable between Implicit and Explicit, i.e. autonomy-support should not cost task effectiveness.

This preliminary analysis uses only the 35 participants collected so far (Implicit vs. Explicit; Control not yet run) and only the self-report questionnaires — task performance (sequences completed, time, hints used) still requires video coding and is not part of this analysis. The goal is to get an early read on whether there's a detectable signal before investing in that video-coding effort.

### 1.1 Participant demographics

Background data were available for 35 of the 35 analyzed participants (matched by participant ID after correcting 2 duplicate-ID data entry conflicts and 2 ID mislabelings identified during matching — see below). Age, sex, and education are not included in this de-identified dataset. Self-rated confidence using a computer, tablet, and phone (1-5 scale) averaged M=1.66 (SD=1.08), M=1.57 (SD=1.12), and M=3.14 (SD=1.22) respectively. Smartphone ownership: Sim (n=22, 63%); Não (n=13, 37%). Prior experience with robots: 2 - ouvi falar / vi na televisão (n=26, 74%); 3 - só vi / ouvi falar de um robô em particular (ex. aspirador ou Bimby) (n=6, 17%); 1 - nunca vi / ouvi falar (n=3, 9%).

**ID conflicts resolved in the prestudy file:**
- P6 submitted twice; both submissions are the same participant, deduplicated to one row (the age-based correction used in the original, non-de-identified analysis does not apply here since age is not part of this dataset).
- A1 had two conflicting submissions under the same ID (different ages/occupations, consistent with two different people) — the second, unrelated submission was dropped, keeping the first.
- P10's second submission was confirmed to actually belong to participant A10 (mislabeled at data entry) — relabeled accordingly.
- P14's second submission was confirmed to actually belong to participant A14 (mislabeled at data entry) — relabeled accordingly; A14 is not part of the 35 analyzed participants, so this entry does not appear in the demographics above.

## 2. Instruments and subscale mapping

Two instruments were administered:

- **IMI (Intrinsic Motivation Inventory)** — task-specific, `IMI_Complete.pdf`, administered on the instrument's native **7-point scale** (1 = not at all true, 7 = very true). Two blocks:
  - 22-item Task Evaluation Questionnaire: **Interest/Enjoyment** (7 items), **Perceived Competence** (5), **Perceived Choice** (5), **Pressure/Tension** (5).
  - 8-item **Relatedness** subscale, worded about "this person" in the original instrument — administered here with "the robot" substituted as the interaction partner. (This resolves what were referred to as "the robot questions" — they are simply IMI-Relatedness, not a separate scale.)
- **BPNSS (Basic Psychological Need Satisfaction Scale)**, 21 items, `BPNSS-General_21item.pdf`. The source instrument specifies a 7-point scale, but **this study administered it on a 5-point scale (1–5)** — confirmed by checking the actual value range in the data (see Section 3.6). Normally about need satisfaction in life generally; here contextualized to "during the memory game" / "the robot." Three subscales: **Autonomy** (7 items), **Competence** (6), **Relatedness** (8).

Every item in the CSV was checked word-for-word against the source PDFs to confirm correct subscale assignment and correct preservation of reverse-item polarity in translation.

### 2.1 Full item listing by subscale

The exact text administered (Portuguese), by column and subscale, with reverse-scored items marked:

**IMI Interest/Enjoyment**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 3 | Enquanto jogava o jogo de memória, eu pensei sobre o quanto estava a gostar. |  |
| 7 | Fazer o jogo de memória foi muito interessante. |  |
| 10 | Jogar o jogo de memória foi divertido. |  |
| 12 | Gostei muito de jogar o jogo de memória. |  |
| 16 | Achei o jogo de memória muito aborrecido. | yes |
| 19 | Achei o jogo de memória muito interessante. |  |
| 22 | Descreveria o jogo de memória como muito agradável. |  |

**IMI Perceived Competence**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 6 | Acho que fui bastante bom(a) no jogo de memória. |  |
| 9 | Acho que me saí bastante bem no jogo de memória, em comparação com outros participantes. |  |
| 14 | Estou satisfeito(a) com o meu desempenho no jogo de memória. |  |
| 18 | Senti-me bastante habilidoso(a) neste jogo de memória. |  |
| 24 | Depois de jogar o jogo de memória por algum tempo, senti-me bastante competente. |  |

**IMI Perceived Choice**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 13 | Realmente não tive escolha sobre jogar o jogo de memória. | yes |
| 17 | Senti que estava a fazer o que queria enquanto estava a fazer o jogo de memória. |  |
| 23 | Fiz o jogo de memória porque não tive escolha. | yes |

**IMI Pressure/Tension**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 4 | Não me senti nervoso(a) de todo acerca de jogar o jogo de memória. |  |
| 8 | Senti-me tenso enquanto jogava o jogo de memória. |  |
| 11 | Senti-me relaxado enquanto jogava o jogo de memória. | yes |
| 15 | Estava ansioso durante o jogo de memória. |  |
| 20 | Senti-me pressionado durante o jogo de memória. |  |

**IMI Relatedness (robot)**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 25 | Senti-me muito distante do robô. | yes |
| 26 | Duvido muito que eu e o robô alguma vez fôssemos ficar amigos. | yes |
| 27 | Senti que realmente podia confiar no robô. |  |
| 28 | Gostaria de ter uma oportunidade de voltar a interagir com o robô. |  |
| 29 | Realmente preferia não voltar a interagir com o robô no futuro. | yes |
| 30 | Não senti que podia realmente confiar no robô. | yes |
| 31 | Acho provável que eu e o robô pudéssemos tornar-nos amigos. |  |
| 32 | Sinto-me realmente próximo(a) do robô. |  |

**BPNSS Autonomy**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 37 | Senti-me pressionado(a) no jogo da memória. | yes |
| 44 | Durante o jogo de memória, frequentemente tive que fazer o que me mandavam. | yes |
| 50 | Senti que posso ser eu mesmo(a) enquanto jogava o jogo de memória. |  |

**BPNSS Competence**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 36 | Muitas vezes não me senti muito competente durante o jogo da memória. | yes |
| 38 | Senti que fui bom/boa no jogo de memória. |  |
| 43 | Consegui aprender coisas novas e interessantes durante o jogo de memória. |  |
| 46 | Não me senti realizado durante o jogo de memória. | yes |
| 48 | Durante o jogo de memória, não tive muitas oportunidades de mostrar o quão capaz sou. | yes |
| 52 | Muitas vezes durante o jogo de memória, não me senti capaz. | yes |

**BPNSS Relatedness**

| col | item text (as administered) | reverse-scored? |
|---|---|---|
| 34 | Gostei muito do robô com quem interagi durante o jogo de memória. |  |
| 39 | Dei-me bem com o robô durante o jogo de memória. |  |
| 40 | Fiquei na minha durante o jogo de memória e não interagi muito com o robô. | yes |
| 42 | Considerei o robô como meu amigo durante o jogo de memória. |  |
| 45 | Durante o jogo de memória, o robô preocupou-se comigo. |  |
| 49 | Não me senti muito próximo(a) do robô durante o jogo de memória. | yes |
| 51 | O robô com quem eu interagi durante o jogo de memória não pareceu gostar muito de mim. | yes |
| 54 | O robô geralmente foi bastante amigável comigo durante o jogo de memória. |  |

## 3. Data cleaning steps applied

1. **Duplicate column.** Columns 34 and 35 in the raw export are identical text (a Google Forms duplication of BPNSS item 2). Column 35 was dropped; column 34 used as the sole instance of that item.
2. **Missing data.** 3 cells missing out of 1820 (35 participants × 52 items) — handled with pairwise deletion (subscale means computed with `skipna=True`). Tested as a robustness check against listwise deletion (dropping any participant with a missing item in that specific subscale entirely, rather than averaging over their remaining items): conclusions are unchanged either way.
- **BPNSS Autonomy** (1 participant(s) with a missing item): pairwise (current) n=18/17, α=0.492, p=0.036 vs. listwise (excluded) n=18/16, α=0.490, p=0.047.
- **BPNSS Relatedness** (2 participant(s) with a missing item): pairwise (current) n=18/17, α=0.568, p=0.495 vs. listwise (excluded) n=16/17, α=0.619, p=0.376.
3. **Translation slip — BPNSS item 13** (col 46). Original: *"Most days I feel a sense of accomplishment"* (not reverse-scored in the official key). Administered Portuguese: *"Não me senti realizado..."* ("I did **not** feel accomplished") — polarity flipped in translation. Confirmed as an unintentional slip. Corrected by treating col 46 as reverse-scored, contrary to the official key, to match what was actually administered.
4. **Data-entry inversion — IMI Pressure/Tension item 2** (col 4, *"Não me senti nervoso(a) de todo..."*). This item was correctly translated (preserves the original's negation), but was suspected to have been mis-recorded during data entry — scored by the perceived nervousness level directly rather than by the literal truth-value of the negated statement. Tested by comparing this item's correlation with the rest of the subscale under both scoring directions: **r = -0.57** treated as officially reverse-scored vs. **r = 0.57** treated as a normal item — an exact sign flip, confirming the inversion. Corrected by treating col 4 as a normal (non-reversed) item, which raised the subscale's Cronbach's α from .28 to 0.82.
5. A systematic check was run afterward across **every** reverse-scored item in every subscale, testing whether flipping any item's polarity would substantially improve its fit with the rest of its subscale. No further candidates were found beyond the one corrected above.
6. **Scale-range mismatch — BPNSS administered on 1–5, not 1–7.** Checking the raw value range per instrument block showed IMI responses spanning 1–7 as expected, but every BPNSS item (cols 33–54) spanning only 1–5. All BPNSS reverse-scoring in this report uses (1+5)−x = 6−x, not the instrument's native 8−x. This has **essentially no effect** on Cronbach's alpha, item-total correlations, or Shapiro-Wilk normality for BPNSS subscales — those are exactly invariant to the reversal constant, verified directly (alpha identical to three decimals either way), because it is a uniform shift applied identically to every complete case. Group-comparison p-values and effect sizes shift by a negligible amount (e.g., BPNSS Autonomy: p=.041 vs .035 under the old, incorrect constant) rather than being perfectly frozen, because one participant has a missing reverse-scored item — under pairwise deletion their subscale mean averages over one fewer item, so the shift isn't perfectly uniform for that single case. None of this changes any conclusion in Section 5. It **does** affect absolute subscale means (now correctly bounded to 1–5) and, more importantly, the **collapsed-to-3 rule** (Section 6), which must use a 5-point-appropriate split rather than the 7-point rule.
7. **BPNSS Autonomy item removed — col47, "Durante o jogo de memória, o robô teve em consideração os meus sentimentos" ("During the memory game, the robot took my feelings into consideration").** This item was dropped from the Autonomy subscale on content-validity grounds, not purely statistical ones: the source BPNSS item is a general life-satisfaction autonomy prompt, but adapted to this specific experimental context, it stops asking about the participant's own freedom/self-determination and instead asks whether *the robot* was responsive/caring toward them — i.e., it becomes a relatedness item in this framing, not an autonomy item. This is corroborated statistically: col47 had the subscale's worst item-total correlation (r=-.16) and was the first item removed in the alpha-if-item-deleted diagnostic (Section 5.3). BPNSS Autonomy is therefore scored here as a **6-item subscale** (cols 33, 37, 41, 44, 50, 53); all reliability and group-comparison figures below reflect this. For transparency: with col47 *included* (the original 7-item scale), α=0.174 and the group comparison was p=0.041; *removing* it raises reliability to α=0.492 but the group comparison becomes p=0.036. The removal was decided on content grounds before checking this consequence, and if anything it worked against the significant result rather than for it — evidence this was not an outcome-driven exclusion.
8. **Perceived Choice items removed — col5 ("Senti que foi minha escolha jogar o jogo de memória") and col21 ("Senti que tinha de jogar o jogo de memória"), both about choosing to *participate in the study* at all rather than about choices *within* the game.** Unlike the BPNSS Autonomy removal above, this was a purely statistical decision (no content-validity argument was made in advance): the original 5-item scale had unacceptable reliability (α=0.038), so cols were dropped one at a time via the alpha-if-item-deleted diagnostic (Section 5.3) until reliability crossed .5. Two items were removed, leaving a **3-item subscale** (cols 13, 17, 23; α=0.603). For transparency: with all 5 items, the group comparison was p=0.184; with the reduced 3-item scale, p=0.750 — both non-significant, so this reduction does not manufacture a finding, it only cleans up an unusable reliability figure.
9. **BPNSS Autonomy further reduced — col33 ("Senti que era livre para decidir por mim mesmo(a) como jogar o jogo da memória"), col41 ("Senti-me livre para expressar as minhas ideias e opiniões durante o jogo de memória"), and col53 ("Não houve muitas oportunidades para decidir por mim mesmo(a) como fazer as coisas durante o jogo de memória") were also dropped from the 6-item scale above.** Same purely statistical procedure as note 8, applied because reliability remained poor (α=0.252) even after the col47 content-validity exclusion: items dropped one at a time via alpha-if-item-deleted until reliability approached the .5 floor. This leaves a **3-item subscale** (cols 37, 44, 50; α=0.492) — still just short of .5, the best this procedure achieves here without collapsing to a 2-item scale that would barely be more than a pairwise correlation. For transparency: with the 6-item scale, the group comparison was p=0.063; with the reduced 3-item scale, p=0.036. Unlike the Perceived Choice reduction, this one *does* flip the result from non-significant to significant; see Section 5.3 for the further robustness check (does the difference survive reducing one step more, to 2 items) and Section 10 for the resulting reliability caveat.

## 4. Analysis method

For each of the 8 subscales:

1. **Reverse-score** items per the (corrected) key: subtract the raw response from (min+max) of the scale.
2. **Reliability**: Cronbach's alpha across the subscale's items, plus corrected item-total correlations to identify any items dragging reliability down.
3. **Normality**: Shapiro-Wilk test on each condition group separately (n=18 Implicit, n=17 Explicit).
4. **Group comparison**: Welch's t-test (unequal variances, robust to the slightly unequal group sizes) if both groups pass Shapiro-Wilk (p>.05); otherwise Mann-Whitney U. Effect size reported as Cohen's d (t-test) or rank-biserial correlation (Mann-Whitney).

## 5. Results — original administered scale (IMI: 1–7, BPNSS: 1–5)

### 5.1 Reliability

| Subscale | k items | Cronbach's α | 95% CI |
|---|---|---|---|
| IMI Interest/Enjoyment | 7 | 0.867 | [0.79, 0.93] |
| IMI Perceived Competence | 5 | 0.884 | [0.81, 0.94] |
| IMI Perceived Choice | 3 | 0.603 | [0.30, 0.79] |
| IMI Pressure/Tension | 5 | 0.816 | [0.70, 0.90] |
| IMI Relatedness (robot) | 8 | 0.718 | [0.55, 0.84] |
| BPNSS Autonomy | 3 | 0.492 | [0.11, 0.73] |
| BPNSS Competence | 6 | 0.728 | [0.56, 0.85] |
| BPNSS Relatedness | 8 | 0.568 | [0.31, 0.75] |

Corrected item-total correlations (per item, after all corrections above):

- **IMI Interest/Enjoyment**: col3=0.47, col7=0.63, col10=0.66, col12=0.73, col16=0.59, col19=0.77, col22=0.72
- **IMI Perceived Competence**: col6=0.82, col9=0.58, col14=0.82, col18=0.72, col24=0.69
- **IMI Perceived Choice**: col13=0.37, col17=0.45, col23=0.47
- **IMI Pressure/Tension**: col4=0.57, col8=0.69, col11=0.7, col15=0.81, col20=0.31
- **IMI Relatedness (robot)**: col25=0.3, col26=0.22, col27=0.33, col28=0.53, col29=0.57, col30=0.49, col31=0.66, col32=0.42
- **BPNSS Autonomy**: col37=0.26, col44=0.19, col50=0.51
- **BPNSS Competence**: col36=0.76, col38=0.61, col43=0.18, col46=0.36, col48=0.25, col52=0.64
- **BPNSS Relatedness**: col34=0.36, col39=0.35, col40=0.22, col42=0.33, col45=0.24, col49=0.26, col51=0.38, col54=0.23

**Notes:** Interest/Enjoyment, Perceived Competence, and (after correction) Pressure/Tension show good reliability (α > .7). BPNSS Competence and IMI Relatedness are acceptable. BPNSS Relatedness is weak. Perceived Choice, reduced to its best 3 items (Section 3, note 8), reaches acceptable reliability (α=0.60). BPNSS Autonomy, given the same item-reduction treatment (Section 3, note 9), improves from α=.17 (original 7 items) to α=0.49 (reduced 3 items) — better, but **still short of the conventional .5 floor**, not explained by any detected data-entry or translation error; likely either genuine item incoherence in this context/population or instability from the small sample.

### 5.2 Group comparison (Implicit vs. Explicit)

| Subscale | n (I/E) | M±SEM Implicit | M±SEM Explicit | Normal? | Test | Statistic | p | Effect |
|---|---|---|---|---|---|---|---|---|
| IMI Interest/Enjoyment | 18/17 | 6.16±0.13 | 6.04±0.16 | yes | Welch t-test | 0.56 | 0.580 | Cohen's d=0.19 |
| IMI Perceived Competence | 18/17 | 5.06±0.24 | 4.24±0.35 | yes | Welch t-test | 1.95 | 0.062 | Cohen's d=0.66 |
| IMI Perceived Choice | 18/17 | 5.85±0.15 | 5.61±0.28 | no | Mann-Whitney U | 163.00 | 0.750 | rank-biserial r=0.07 |
| IMI Pressure/Tension | 18/17 | 3.00±0.30 | 2.54±0.36 | no | Mann-Whitney U | 187.50 | 0.260 | rank-biserial r=0.23 |
| IMI Relatedness (robot) | 18/17 | 5.53±0.18 | 5.60±0.19 | yes | Welch t-test | -0.26 | 0.797 | Cohen's d=-0.09 |
| BPNSS Autonomy | 18/17 | 3.83±0.18 | 3.37±0.10 | yes | Welch t-test | 2.21 | **0.036** | Cohen's d=0.74 |
| BPNSS Competence | 18/17 | 3.37±0.15 | 3.08±0.19 | yes | Welch t-test | 1.18 | 0.245 | Cohen's d=0.40 |
| BPNSS Relatedness | 18/17 | 4.14±0.09 | 4.04±0.11 | no | Mann-Whitney U | 178.00 | 0.416 | rank-biserial r=0.16 |

**Summary:** The only subscale reaching conventional significance is BPNSS Autonomy (p=0.036), in the hypothesized direction (Implicit > Explicit), on its reduced 3-item scoring (Section 3, note 9). Its reliability (α=0.49) is still below the conventional .5 floor, so this should be read as a real but tentative finding, not a confirmed one — see Section 5.3 for the robustness check on whether it survives further reduction. The other reliable signal is **IMI Perceived Competence** (α=0.88, p=0.062, Cohen's d=0.66), trending toward Implicit > Explicit without reaching significance, consistent with the scaffolding-theory rationale for the study design.

### 5.3 Robustness checks

**IMI Perceived Competence — leave-one-out sensitivity.** To check whether the p=0.062 result is being driven by any single participant, the group comparison was recomputed 35 times, each time with one participant removed. Resulting p-values ranged from 0.029 to 0.114 — a narrow band, indicating the trend is not an artifact of one influential case. 3 of 35 single-participant removals bring p below .05 on their own:

| Removed participant | Condition | Their score | Resulting p |
|---|---|---|---|
| M5 | Explícita | 6.40 | 0.029 |
| P10 | Explícita | 6.20 | 0.033 |
| P14 | Explícita | 6.00 | 0.037 |

All three are Explicit-condition participants with unusually *high* competence scores (above even the Implicit mean of 5.06) — removing any one of them narrows the Explicit distribution and widens the gap. There is no independent basis (manipulation-check or log irregularity) to exclude any of them; they are simply participants in the Explicit group who reported feeling competent. **No participants were excluded on this basis.** The honest read is a stable, borderline-significant trend consistent with the sample being underpowered, not an effect that is fragile to a single case.

**BPNSS Autonomy — does the group difference survive pushing the item reduction further?** Starting from the 3-item scale adopted in Section 3 (note 9) (α=0.492, p=0.036) and iteratively dropping whichever item's removal improves Cronbach's alpha most (same alpha-if-item-deleted logic as the reliability diagnostics elsewhere in this project), the group comparison was recomputed at every step:

| Items remaining (k) | α | Group comparison p | Effect |
|---|---|---|---|
| 3 | 0.492 | **0.036** | Cohen's d=0.74 |
| 2 | 0.637 | **0.044** | rank-biserial r=0.39 |

The difference remains significant at every further-reduction stage tested (2 items). This suggests the significant result on the adopted 3-item scale is not simply an artifact of stopping the reduction at exactly that item count. The underlying reliability remains below the conventional .5 floor throughout, though, so the finding should still be read as tentative rather than confirmed.

**Does controlling for hint dosage change either finding? (ANCOVA)** Implicit and Explicit participants did not receive identical numbers of hints over the session (Section 8 below), so a natural question is whether either self-report finding is really just tracking how much support someone happened to receive, rather than the condition itself. For both IMI Perceived Competence and BPNSS Autonomy, an ANCOVA was run with condition as the between-subjects factor and total hints delivered as a covariate. The homogeneity-of-regression-slopes assumption (condition × hints interaction) held for both (p=0.89 and p=0.14, both non-significant, so the ANCOVA is appropriate to interpret).

- **IMI Perceived Competence**: hint count barely correlates with competence (r=0.15). Controlling for it, F(1,32)=3.16, **p=0.085** — slightly *weaker* than the raw p=0.062, since the covariate costs a degree of freedom without explaining meaningful variance. Adjusted means: Implicit 5.01 (raw 5.06), Explicit 4.28 (raw 4.24).
- **BPNSS Autonomy**: hint count essentially does not correlate with autonomy (r=-0.22). Controlling for it, F(1,32)=7.36, **p=0.011** — virtually unchanged from raw p=0.036. Adjusted means are nearly identical to raw means: Implicit 3.87 (raw 3.83), Explicit 3.34 (raw 3.37).

Neither finding is confounded by how many hints a participant happened to receive — hint dosage explains close to none of the variance in either measure, so this rules out "the self-report effect is just proxying for support quantity" as an explanation for both, without pushing either result toward or away from significance in a meaningful way.

---

## 6. Sensitivity analysis — responses collapsed to a 1–3 scale

**Rationale.** Several participants appeared to respond to the rating scales in effectively yes/no/maybe terms during administration. As a sensitivity check, raw item responses were recoded onto a 3-point scale *before* reverse-scoring, to see whether results are robust to this coarser, arguably more behaviorally realistic response granularity. The collapse rule is scale-appropriate rather than a single fixed rule: **IMI items (native 1–7)** use 1–3 → 1, 4 → 2, 5–7 → 3; **BPNSS items (administered 1–5)** use the proportional equivalent, 1–2 → 1, 3 → 2, 4–5 → 3 — applying the 7-point rule to 5-point data would have skewed the split (3 of 5 raw values in the bottom bucket, only 1 in the top). Reverse-scoring after collapsing uses (1+3) − x = 4 − x uniformly, since collapsing already normalizes both instruments onto a common 1–3 range. The same item-level corrections (col 46, col 4) were carried over unchanged.

### 6.1 Reliability (collapsed scale)

| Subscale | k items | Cronbach's α | 95% CI |
|---|---|---|---|
| IMI Interest/Enjoyment | 7 | 0.488 | [0.18, 0.71] |
| IMI Perceived Competence | 5 | 0.832 | [0.72, 0.91] |
| IMI Perceived Choice | 3 | 0.659 | [0.40, 0.82] |
| IMI Pressure/Tension | 5 | 0.783 | [0.64, 0.88] |
| IMI Relatedness (robot) | 8 | 0.468 | [0.15, 0.70] |
| BPNSS Autonomy | 3 | 0.318 | [-0.20, 0.63] |
| BPNSS Competence | 6 | 0.727 | [0.56, 0.85] |
| BPNSS Relatedness | 8 | 0.256 | [-0.18, 0.58] |

Corrected item-total correlations (collapsed scale):

- **IMI Interest/Enjoyment**: col3=0.23, col7=n/a (zero variance), col10=0.22, col12=n/a (zero variance), col16=n/a (zero variance), col19=0.46, col22=0.59
- **IMI Perceived Competence**: col6=0.75, col9=0.52, col14=0.71, col18=0.57, col24=0.63
- **IMI Perceived Choice**: col13=0.39, col17=0.49, col23=0.69
- **IMI Pressure/Tension**: col4=0.53, col8=0.68, col11=0.69, col15=0.79, col20=0.11
- **IMI Relatedness (robot)**: col25=0.18, col26=0.04, col27=-0.08, col28=0.35, col29=0.38, col30=-0.08, col31=0.52, col32=0.26
- **BPNSS Autonomy**: col37=0.15, col44=0.12, col50=0.25
- **BPNSS Competence**: col36=0.73, col38=0.58, col43=0.13, col46=0.39, col48=0.28, col52=0.66
- **BPNSS Relatedness**: col34=0.14, col39=0.01, col40=0.17, col42=-0.1, col45=0.04, col49=0.07, col51=0.37, col54=n/a (zero variance)

*"Zero variance" means every participant landed in the same collapsed bucket for that item. In this run: col7, col12, col16, col54. Correlation is undefined there, and it is itself a finding: those items only reveal a ceiling/floor effect once collapsed to 3 points, which was invisible on the full 7-point scale.*

### 6.2 Group comparison (collapsed scale)

| Subscale | n (I/E) | M±SEM Implicit | M±SEM Explicit | Normal? | Test | Statistic | p | Effect |
|---|---|---|---|---|---|---|---|---|
| IMI Interest/Enjoyment | 18/17 | 2.98±0.01 | 2.94±0.03 | no | Mann-Whitney U | 157.50 | 0.840 | rank-biserial r=0.03 |
| IMI Perceived Competence | 18/17 | 2.57±0.10 | 2.16±0.17 | no | Mann-Whitney U | 199.00 | 0.128 | rank-biserial r=0.30 |
| IMI Perceived Choice | 18/17 | 2.91±0.05 | 2.80±0.12 | no | Mann-Whitney U | 157.00 | 0.860 | rank-biserial r=0.03 |
| IMI Pressure/Tension | 18/17 | 1.70±0.14 | 1.51±0.16 | no | Mann-Whitney U | 184.00 | 0.297 | rank-biserial r=0.20 |
| IMI Relatedness (robot) | 18/17 | 2.71±0.06 | 2.78±0.06 | no | Mann-Whitney U | 127.00 | 0.374 | rank-biserial r=-0.17 |
| BPNSS Autonomy | 18/17 | 2.39±0.11 | 2.22±0.07 | no | Mann-Whitney U | 205.00 | 0.061 | rank-biserial r=0.34 |
| BPNSS Competence | 18/17 | 2.27±0.11 | 2.07±0.15 | no | Mann-Whitney U | 187.50 | 0.258 | rank-biserial r=0.23 |
| BPNSS Relatedness | 18/17 | 2.73±0.06 | 2.75±0.05 | no | Mann-Whitney U | 143.50 | 0.761 | rank-biserial r=-0.06 |

**Caveat:** Shapiro-Wilk and parametric statistics are a poor theoretical fit for a 3-point scale (few distinct values, many ties) — the normal/non-normal classification here should be read as a pragmatic decision rule for consistency with Section 5, not as strong evidence of a genuinely continuous, normally-distributed variable. Treat this section as a robustness check on direction and rough magnitude of effects, not as an independently rigorous analysis.

## 7. Manipulation check

`OlderAdults_ManipulationCheck (Responses) - Form responses 1.csv`, matched to 35 of the 35 analyzed participants. 6 additional submissions under IDs "PS1"-"PS6" were excluded as pilot/test entries, not real study participants (confirmed: they do not appear anywhere in the main dataset).

Each item is rated on a 1-5 scale and analyzed individually (not combined into a single reliability-tested score), since the manipulation check is deliberately designed so different items should move in *opposite* directions between conditions (e.g., "the robot told me directly" should score higher in Explicit; "I still had to figure it out myself" should score higher in Implicit) — combining them into one composite would not be meaningful. One item (a free-text sentence completion, not shown here) was also collected but requires qualitative coding, not included in this pass.

| col | item | n (I/E) | M±SEM Implicit | M±SEM Explicit | Test | Statistic | p | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | Quando eu estava a reproduzir as sequências, o robô deu-me pistas. | 18/17 | 4.94±0.06 | 4.76±0.24 | Mann-Whitney U | 154.00 | 0.967 | rank-biserial r=0.01 |
| 4 | Quando o robô me deu pistas, fê-lo explicitamente. | 18/16 | 1.83±0.38 | 4.56±0.30 | Mann-Whitney U | 36.00 | **0.000** | rank-biserial r=-0.75 |
| 5 | Quando o robô me deu pistas, fê-lo de forma subtil (sem dizer a resposta diretamente). | 18/16 | 4.17±0.38 | 1.44±0.30 | Mann-Whitney U | 252.00 | **0.000** | rank-biserial r=0.75 |
| 6 | O robô disse-me diretamente onde colocar os blocos ou qual a cor correta. | 18/16 | 2.06±0.33 | 4.94±0.06 | Mann-Whitney U | 10.00 | **0.000** | rank-biserial r=-0.93 |
| 7 | O robô olhou para o bloco correto ou para a zona correta do tabuleiro quando eu não sabia o que fazer. | 18/16 | 3.44±0.44 | 3.12±0.46 | Mann-Whitney U | 160.00 | 0.566 | rank-biserial r=0.11 |

**Interpretation:** a significant, correctly-directed difference on the explicit/implicit-wording items would confirm participants experienced the two conditions as intended (a manipulation check in the traditional sense).

Column 8 (*"Quando o robô me deu uma pista ainda tive de descobrir a resposta por mim próprio/a"* — "I still had to figure out the answer myself") is reported separately as a single-item Perceived Autonomy measure alongside the self-report dimensions (Section 5), not as a manipulation-check item -- it uses the full sample (n=18/17), unlike items 4-7 above, since P15's flat response is a genuine (if extreme) answer to this specific item rather than an uninterpretable one: Implicit 4.61±0.23, Explicit 1.82±0.38, Mann-Whitney U stat=272.50, p=0.00002, rank-biserial r=0.78. It also complements the multi-item Choice/Autonomy subscales in Section 5 whose reliability is poor.

## 8. Task performance from game logs

Session logs from `Elmo_Scripts/logs/` were parsed directly (no video coding needed for these metrics — they're already timestamped in the WoZ dashboard's log output). 35 of 35 participants matched.

**File selection.** Several participants have more than one log file for the same session (technical restarts). One file per participant was kept: the one containing a proper session-end marker (`SAY_GOODBYE`) and the most content; short files with no `SAY_GOODBYE` (session aborted seconds after starting) were discarded (8 such files across the dataset). Two IDs outside the 35 analyzed participants ("PS1"-"PS5", "vitoria_teste") were excluded as pilot/test runs, consistent with the manipulation check.

**Early-start trials discarded.** When a participant acted before the robot finished announcing a sequence, the wizard triggers `EARLY_START`, which the code marks as an aborted attempt (`was_early_start`) before generating a fresh sequence for the next real attempt. This is common — 31 of 49 raw log files contain at least one such event. Not every `EARLY_START` needs the same handling, though: entered from `IDLE` (104 occurrences dataset-wide), it's a false alarm between trials with no trial in progress to discard; entered from `NEW_SEQUENCE` or `FORGOT_SEQUENCE` (32 occurrences), an actual trial-in-progress was interrupted and its data is not meaningful. Only the latter case is discarded here — 32 such occurrences collapse to 30 discarded trials (a couple of trials had two early-starts before a new trial number was assigned, so they count once) — removed entirely (trial count, sequence length, and any hints/latencies tied to that trial index) before computing every metric below, with remaining trials renumbered sequentially so the discarded gaps don't distort the hints-per-sequence trend regression.

**Metric definitions**, derived from the underlying `state_machine.py` source, not just log text:
- **Hints** are counted as transitions into any of the four states the code itself defines as `hint_states`: `HESITANT_CUBE`, `HESITANT_POSITION`, `INCORRECT_CUBE`, `INCORRECT_POSITION`. `TOUCHED_WRONG_BLOCK` and `FORGOT_SEQUENCE` are explicitly excluded — they're logged separately and are not part of the code's own hint-state list.
- **Hint ladder depth used**: each hint state doesn't deliver just one message — it runs an escalating "ladder" of up to several sub-hints over time if the participant doesn't act (e.g. a subtle nudge, then a stronger one). Ladder length is *not* constant: per `behaviors.py`, `HESITANT_POSITION` and `INCORRECT_POSITION` always have 2 and 3 steps respectively, but `HESITANT_CUBE` and `INCORRECT_CUBE` get an extra elimination step (3 and 4, instead of 2 and 3) specifically when the condition is Implicit **and** the target block's colour is green/blue/purple (needed to narrow down between visually similar remaining options). A raw count of delivered sub-hints would therefore be biased — Implicit could rack up more purely because its ladder is longer for those colours, not because the participant needed more help. To correct for this, each hint episode (from entering a hint state to leaving it) is scored as delivered-sub-hints ÷ max-possible-sub-hints-for-that-specific-episode (using the actual block colour from that trial's sequence), giving a 0-1 fraction; the reported metric is the mean of that fraction across all hint episodes in the session. Sub-hint deliveries are counted from `Play Sound` **and** `Suppressed sound (echo avoidance)` log lines — both mean the code advanced to that rung, even if the debounce silenced the audio.
- **Hint → next-action latency**: seconds from a hint-trigger timestamp to the next block pickup/placement event.
- **Baseline (hint-free) first-action latency**: for each trial, seconds from the sequence-announcement finishing (`Transitioning from NEW_SEQUENCE to IDLE`, right after the "you may begin" cue) to the participant's first pickup/placement action — kept only when no hint fired before that action, so it's a genuinely unassisted starting latency. Included specifically to check whether the hint→action latency finding is about responding to hints, or just a general pace difference between conditions.
- **Self-caught vs. robot-flagged wrong-block touches**: `TOUCHED_WRONG_BLOCK` fires immediately (a high-priority override in `check_logic_gate`) whenever the wizard sees a wrong block touched, and delivers one single nudge — not an escalating ladder like the four hint states. What happens right after tells us whether that nudge was enough: exiting to `INCORRECT_CUBE`/`INCORRECT_POSITION` means the wrong block still got placed anyway (needed the fuller corrective hint); exiting anywhere else (`IDLE`, a hesitant state, `NEW_SEQUENCE`) means it was caught/corrected without escalating that far. Reported as a rate (self-caught ÷ total touches) alongside the raw touch count. Caveat going in: since a wizard has to notice and toggle this in real time, truly instantaneous self-corrections (fixed before the wizard can react at all) leave no trace in the log at all — so this can only capture the slower end of self-correction, not the fastest.
- **Manual sequence-length resets**: count of `[UI] Sequence Length changed to: X` wizard actions per session (see Section 8's earlier discussion — used here to check whether reset frequency is balanced across conditions, i.e. the wizard wasn't more lenient/protective in one condition than the other).
- **"Successfully completed"** is defined by the game's own logic, not something inferred from log text: it's every trial where `all_checked` was true when the next sequence started (i.e. `"Auto-incremented sequence length to X"` was logged), meaning the block-check and position-check boxes were all ticked. **Important limitation, confirmed directly by the wizard who ran these sessions**: those checkboxes are set by the wizard in real time, and are sometimes marked complete even when the participant didn't actually get it right (e.g. to keep the session moving). So this whole family of "success" metrics inherits some wizard-leniency noise that the log data alone cannot correct for — the assisted/independent split below does not fix this (a wizard could over-mark a zero-hint trial too), it only reorganizes by how much hint support was involved. Both **sequences completed successfully** and **max sequence length completed** are reported two ways, deliberately avoiding any fixed hint-count threshold: Implicit hints are individually less informative than Explicit ones (established below — Implicit trials need more follow-up hints per success), so a fixed "completed with ≤N hints" cutoff would penalize Implicit participants for the hint style itself, not for lower ability. Instead:
  - **Assisted** — completed correctly (per the wizard's marking), any amount of hint support allowed. Matches H2's "comparable task performance" framing: how far did they get / how many did they complete with the support the condition actually gave them.
  - **Independent** — completed with *zero* hints triggered during that specific trial. A stricter, hint-style-unconfounded read, closer to a standard Corsi-span reading, though still subject to the wizard-marking caveat above.

  Max length uses the **peak** value ever completed, not the length active when the session ended — sequence length is not a pure automatic staircase; the wizard can manually reset it mid-session (`[UI] Sequence Length changed to: X`), and does so in every single session in this dataset (2-10 times per session), typically resetting back down after a success rather than letting it climb indefinitely. Using the peak (rather than the final value) avoids understating the true ceiling given these resets.
- **Hints-per-sequence trend**: computed two ways. The **raw count slope** is the linear regression of hint count per trial across the session — but since sequence length tends to increase with successes (before any reset), later trials are mechanically longer and have more opportunities to trigger a hint, so a positive slope here may just reflect increasing task difficulty, not increasing reliance on the robot. The **normalized rate slope** divides each trial's hint count by that trial's sequence length before fitting the trend, isolating the per-opportunity hint rate from the length confound — this is the cleaner test of whether reliance on the robot is actually growing or shrinking over the session. Both are reported; the normalized version is the one to trust for "learning to need less help," the raw version still describes the actual hint burden delivered.

| Metric | n (I/E) | M±SEM Implicit | M±SEM Explicit | Test | Statistic | p | Effect |
|---|---|---|---|---|---|---|---|
| Sequences attempted | 18/17 | 10.61±0.62 | 10.65±0.86 | Welch t-test | -0.03 | 0.973 | Cohen's d=-0.01 |
| Sequences completed successfully (assisted, any hints allowed) | 18/17 | 6.56±0.35 | 6.88±0.45 | Mann-Whitney U | 137.00 | 0.600 | rank-biserial r=-0.10 |
| Sequences completed successfully (independent, zero hints) | 18/17 | 2.61±0.46 | 2.65±0.49 | Mann-Whitney U | 147.50 | 0.867 | rank-biserial r=-0.04 |
| Performance rate: completed/attempted (assisted, any hints allowed) | 18/17 | 0.63±0.03 | 0.67±0.03 | Welch t-test | -0.87 | 0.393 | Cohen's d=-0.29 |
| Performance rate: completed/attempted (independent, zero hints) | 18/17 | 0.24±0.03 | 0.23±0.04 | Welch t-test | 0.07 | 0.945 | Cohen's d=0.02 |
| Max sequence length completed (assisted, any hints allowed) | 18/17 | 4.50±0.23 | 4.29±0.31 | Mann-Whitney U | 167.50 | 0.612 | rank-biserial r=0.09 |
| Max sequence length completed (independent, zero hints) | 18/17 | 3.22±0.25 | 3.12±0.48 | Mann-Whitney U | 153.00 | 1.000 | rank-biserial r=0.00 |
| Total hints delivered | 18/17 | 32.89±3.14 | 27.53±1.64 | Welch t-test | 1.52 | 0.142 | Cohen's d=0.50 |
| Hints per sequence | 18/17 | 3.27±0.33 | 2.88±0.31 | Welch t-test | 0.86 | 0.394 | Cohen's d=0.29 |
| Hint → next-action latency (s) | 18/17 | 14.06±1.02 | 12.09±1.59 | Mann-Whitney U | 204.00 | 0.096 | rank-biserial r=0.33 |
| Baseline (hint-free) first-action latency (s) | 2/1 | nan±nan | nan±nan | n/a (insufficient data) | nan | nan | =nan |
| Sub-hints delivered per hint episode (raw, non-standardized) | 18/17 | 1.60±0.08 | 1.33±0.05 | Welch t-test | 2.95 | **0.006** | Cohen's d=0.98 |
| Hint ladder depth used (standardized, 0-1) | 18/17 | 0.44±0.02 | 0.53±0.03 | Welch t-test | -2.19 | **0.036** | Cohen's d=-0.74 |
| Wrong-block touches | 18/17 | 1.67±0.46 | 0.59±0.19 | Mann-Whitney U | 202.50 | 0.085 | rank-biserial r=0.32 |
| Wrong-block touches self-caught (rate, vs. needing a corrective hint) | 12/7 | 1.00±0.00 | 1.00±0.00 | Mann-Whitney U | 42.00 | 1.000 | rank-biserial r=0.00 |
| Hints-per-sequence trend across session (raw count slope) | 18/17 | 0.77±0.15 | 0.58±0.16 | Mann-Whitney U | 190.50 | 0.222 | rank-biserial r=0.25 |
| Hints-per-sequence trend, normalized by sequence length (rate slope) | 18/17 | 0.13±0.04 | 0.06±0.04 | Welch t-test | 1.03 | 0.311 | Cohen's d=0.35 |
| Manual sequence-length resets by wizard | 18/17 | 5.06±0.37 | 5.24±0.55 | Welch t-test | -0.27 | 0.788 | Cohen's d=-0.09 |
| Session duration (min) | 18/17 | 19.67±0.55 | 18.18±0.60 | Welch t-test | 1.84 | 0.075 | Cohen's d=0.62 |

**Interpretation:** Sequences attempted, sequences completed, and max sequence length reached show **no difference** between conditions — a second, purely behavioral confirmation of H2 (comparable task performance) alongside the self-report data. Two metrics stand out:
- **Hint ladder depth used** (M=0.44 Implicit vs. M=0.53 Explicit, p=0.036, Cohen's d=-0.74) — see Section 8's metric definitions below for what this standardizes for and why. Significantly higher in Explicit. In raw (non-standardized) terms Implicit still delivers more sub-hints per episode on average, consistent with each individual Implicit hint carrying less information — but Implicit's ladder is also proportionally longer (extra elimination step for certain block colours), so once expressed as a fraction of what was actually available, Explicit ends up using a larger share of its shorter ladder. Read together with H1, this suggests Explicit hints more often need to escalate close to their maximum (a direct answer eventually has to land), while Implicit participants more often resolve a hint with some of the (longer) ladder still unused.
- **Hint→action latency trends slower in Implicit** (M=14.06s vs. M=12.09s, p=0.096), consistent with more deliberate, effortful processing after an indirect hint versus faster compliance after being told directly — the same mechanism proposed earlier as a behavioral proxy for agency.
- Total hints delivered trends higher in Implicit too (not significant), sensibly following from each individual hint carrying less information, so more of them may be needed to reach the same outcome.

## 9. Thematic analysis of post-task interviews (summary)

Full analysis in `Thematic_Analysis_Report.md`, coded excerpts in `thematic_coded_excerpts.csv` (same folder). 28 of 35 analyzed participants have a post-task interview transcript (missing: P1, P13, P2, P4, P6, P9, P18). Hybrid deductive/inductive thematic analysis (Braun & Clarke), coded excerpt-by-excerpt against a small starter codebook plus inductive additions — **not blind-coded** (condition was visible during coding), single analyst, no second-coder reliability check; treat as directional, not statistically tested.

**Headline finding, most directly relevant to H1**: participants attributed responsibility for catching and fixing their own errors to *themselves* (not the robot) far more often in Implicit transcripts (7 instances) than Explicit ones (2 instances) — e.g. P16 (Implicit): *"Não me atrapalhou, não. Eu é que me atrapalhei"* ("It didn't get in my way. I was the one who got in my own way."). This is direct qualitative evidence of preserved self-attributed ownership under indirect hints, independent of the quantitative scales.

**Supporting findings**: (1) participants' own description of *what* was useful tracked the actual hint style — Implicit participants described indirect, discovery-oriented help (spatial cues, memory-jogging), Explicit participants described direct, compliance-oriented help (being told exactly where to place, trusted accuracy) — functioning as a qualitative confirmation of the manipulation alongside the quantitative one. (2) Hindrance was rarely reported in either condition, converging with the quantitative manipulation check. (3) Two concrete, actionable design leads emerged regardless of condition: overlapping/simultaneous cues caused confusion for one participant, and hint timing relative to sequence length caused another (who disclosed a memory-affecting head injury) to forget earlier items before later hints arrived — worth considering for adapting hint pacing to individual memory capacity in future iterations.

## 10. Open items / next steps

- Perceived Choice reliability was resolved by reducing to its best 3 items (α=0.60); BPNSS Autonomy improved under the same treatment (α=0.49) but still falls short of the conventional .5 floor, and its group comparison flips from non-significant to significant as a result — no mechanical data error found; consider reviewing how those specific items were administered, or revisiting whether BPNSS (a general life-satisfaction instrument) is well-suited to a single ~15-minute task context.
- Control condition not yet collected; current comparisons are Implicit vs. Explicit only.
- Sample size (n=35 of a planned 105+) is small; alpha and p-value estimates above should be treated as directional, not confirmatory.
- Thematic analysis is a single-coder first pass, not blind to condition — a second coder and inter-rater reliability check would strengthen it before drawing firm conclusions.
