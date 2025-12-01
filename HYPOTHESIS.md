# Meta Analysis Hypothesis: 10k+ Trophy Players (Post-Season Changes)

## Research Question
**What deck archetypes and card combinations dominate the competitive meta for players above 10,000 trophies immediately following season changes?**

## Hypothesis

### Primary Hypothesis
Players above 10,000 trophies will converge on 3-5 dominant deck archetypes within the first week of a new season, characterized by:

1. **High skill ceiling cards** - Cards that reward precise timing and positioning
2. **Cycle efficiency** - Low average elixir cost (3.0-3.5) for rapid cycling
3. **Defensive versatility** - Multiple answers to win conditions
4. **Win condition diversity** - Split between beatdown, control, and cycle archetypes

### Secondary Hypotheses

**H1: Card Usage Patterns**
- Champion cards (Monk, Archer Queen, Golden Knight) will appear in >40% of decks
- Evolution cards will have high variance - either meta-defining or absent
- Traditional cycle cards (Ice Spirit, Skeletons, Log) remain staples (>50% usage)

**H2: Archetype Distribution**
- Cycle decks: 35-40% (Hog Cycle, Miner Control, X-Bow)
- Beatdown: 25-30% (Golem, Lava Hound, Giant)
- Bridge Spam: 20-25% (Royal Hogs, Ram Rider, Battle Ram)
- Control: 10-15% (Graveyard, Three Musketeers)

**H3: Meta Shifts Post-Season**
- First 48 hours: High deck diversity as players experiment
- Days 3-5: Rapid convergence on 2-3 dominant archetypes
- Week 2+: Counter-meta decks emerge to combat dominant archetypes

**H4: Trophy Range Stratification**
- 10k-11k players: More varied decks, testing meta
- 11k-12k players: Strong convergence on proven archetypes
- 12k+ players: Innovation within established archetypes

## Methodology

### Data Collection Strategy
1. **Baseline Collection**: Capture current meta state (250 players @ 10k+)
2. **Temporal Sampling**: Collect data at T+0, T+2d, T+5d, T+7d post-season
3. **Control Group**: Compare against 8k-10k trophy players for contrast

### Metrics to Track
- **Card Usage Rate**: % of decks containing each card
- **Win Rate by Card**: Victory % when card is in deck
- **Deck Archetype Distribution**: Classification of deck types
- **Average Elixir Cost**: Trend analysis over time
- **Card Synergy Patterns**: Frequently paired cards
- **Evolution Usage**: Adoption rate of evolution mechanics

### Analysis Plan
1. **Descriptive Statistics**: Usage rates, win rates, deck composition
2. **Trend Analysis**: How meta shifts day-by-day post-season
3. **Comparative Analysis**: 10k+ vs 8k-10k vs general population
4. **Predictive Modeling**: Can we predict meta shifts from early data?

## Expected Outcomes

### What Success Looks Like
1. Clear identification of 3-5 dominant archetypes
2. Statistically significant differences in card usage vs lower trophies
3. Observable convergence pattern in first week
4. Identification of "sleeper" cards gaining popularity

### Potential Confounds
- Balance changes in season update may skew results
- Limited sample size (250 players) may miss niche strategies
- API rate limits may prevent real-time tracking
- Players may copy decks from pros, creating false convergence

## Practical Applications

### For Players
- Identify meta decks to climb ladder efficiently
- Discover counter-decks to dominant archetypes
- Understand trophy-specific meta differences

### For Game Designers
- Balance assessment: Are certain cards overrepresented?
- Meta health: Is diversity sufficient at top level?
- Season impact: How effective are balance changes?

### For Data Science
- Time-series analysis of player behavior
- Network analysis of card synergies
- Predictive modeling of meta evolution

## Database Design Considerations

To support this hypothesis, the database must track:
- Temporal data (battle timestamps for trend analysis)
- Trophy-stratified player segments
- Complete deck compositions per battle
- Win/loss outcomes per card combination
- Game mode filtering (competitive ladder only)

## SQL Query Requirements

Complex queries needed to test hypothesis:
1. **Time-based meta shifts**: JOINs across battles, players, cards with date filters
2. **Trophy-stratified analysis**: Subqueries grouping by trophy ranges
3. **Card synergy detection**: Self-joins on deck_cards to find pairs
4. **Archetype classification**: CASE statements with multiple card conditions
5. **Win rate calculations**: Aggregations with conditional logic

## Timeline

- **T+0 (Season Start)**: Baseline collection (250 players)
- **T+2 days**: Second collection wave
- **T+5 days**: Third collection wave
- **T+7 days**: Final collection + analysis
- **T+10 days**: Report generation and hypothesis validation

## Success Criteria

Hypothesis will be considered **validated** if:
1. ≥70% of players converge on ≤5 archetypes by day 7
2. Clear statistical difference (p<0.05) in card usage vs 8k-10k range
3. Identifiable trend in meta evolution across time points
4. Champion/Evolution cards show >35% usage rate

Hypothesis will be **rejected** if:
- Deck diversity remains high (>10 equally viable archetypes)
- No statistical difference between trophy ranges
- Random walk pattern with no convergence
