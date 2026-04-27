# HELEN Hexagram Pattern Scan

**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Source:** `oracle_hexagram_engine.py` — deterministic rebuild  
**Raw source annotation:** `DRIFT_DETECTED` — trigram annotations not trusted  

---

## HELEN Mode Distribution

| Mode | Count | % | Bar |
|---|---|---|---|
| FOCUS | 16 | 25% | ████████████████ |
| WITNESS | 16 | 25% | ████████████████ |
| ORACLE | 16 | 25% | ████████████████ |
| TEMPLE | 16 | 25% | ████████████████ |

- **Pure mode** (upper == lower family): 16
- **Tension** (upper ≠ lower family): 48

## Trigram Frequency (upper + lower combined, 128 total positions)

| Trigram | Symbol | Mode | Count | % |
|---|---|---|---|---|
| Earth | ☷ | TEMPLE | 16 | 12.5% |
| Mountain | ☶ | WITNESS | 16 | 12.5% |
| Water | ☵ | WITNESS | 16 | 12.5% |
| Wind | ☴ | ORACLE | 16 | 12.5% |
| Thunder | ☳ | FOCUS | 16 | 12.5% |
| Fire | ☲ | ORACLE | 16 | 12.5% |
| Lake | ☱ | TEMPLE | 16 | 12.5% |
| Heaven | ☰ | FOCUS | 16 | 12.5% |

> Each trigram appears exactly 8 times in upper positions and 8 times in lower positions (64 hexagrams × 2 positions ÷ 8 trigrams = 16 each). Deviation signals encoding error.

## Yin/Yang Ratio Distribution (yang:yin)

| Ratio | Count | Hexagrams |
|---|---|---|
| 6:0 | 1 | [1] |
| 5:1 | 6 | [9, 10, 13, 14, 43, 44] |
| 4:2 | 15 | [5, 6, 25, 26, 28, 30, 33, 34, 37, 38, 49, 50, 57, 58, 61] |
| 3:3 | 20 | [11, 12, 17, 18, 21, 22, 31, 32, 41, 42, 47, 48, 53, 54, 55, 56, 59, 60, 63, 64] |
| 2:4 | 15 | [3, 4, 19, 20, 27, 29, 35, 36, 39, 40, 45, 46, 51, 52, 62] |
| 1:5 | 6 | [7, 8, 15, 16, 23, 24] |
| 0:6 | 1 | [2] |

## Opposition Pairs (bitwise complement — all 6 lines flipped)

| Hex A | Glyph A | Hex B | Glyph B | A name | B name |
|---|---|---|---|---|---|
| 1 | ䷀ | 2 | ䷁ | Qián | Kūn |
| 3 | ䷂ | 50 | ䷱ | Zhūn | Dǐng |
| 4 | ䷃ | 49 | ䷰ | Méng | Gé |
| 5 | ䷄ | 35 | ䷢ | Xū | Jìn |
| 6 | ䷅ | 36 | ䷣ | Sòng | Míng Yí |
| 7 | ䷆ | 13 | ䷌ | Shī | Tóng Rén |
| 8 | ䷇ | 14 | ䷍ | Bǐ | Dà Yǒu |
| 9 | ䷈ | 16 | ䷏ | Xiǎo Chù | Yù |
| 10 | ䷉ | 15 | ䷎ | Lǚ | Qiān |
| 11 | ䷊ | 12 | ䷋ | Tài | Pǐ |
| 17 | ䷐ | 18 | ䷑ | Suí | Gǔ |
| 19 | ䷒ | 33 | ䷠ | Lín | Dùn |
| 20 | ䷓ | 34 | ䷡ | Guān | Dà Zhuàng |
| 21 | ䷔ | 48 | ䷯ | Shì Kè | Jǐng |
| 22 | ䷕ | 47 | ䷮ | Bì | Kùn |
| 23 | ䷖ | 43 | ䷪ | Bō | Guài |
| 24 | ䷗ | 44 | ䷫ | Fù | Gòu |
| 25 | ䷘ | 46 | ䷭ | Wú Wàng | Shēng |
| 26 | ䷙ | 45 | ䷬ | Dà Chù | Cuì |
| 27 | ䷚ | 28 | ䷛ | Yí | Dà Guò |
| 29 | ䷜ | 30 | ䷝ | Kǎn | Lí |
| 31 | ䷞ | 41 | ䷨ | Xián | Sǔn |
| 32 | ䷟ | 42 | ䷩ | Héng | Yì |
| 37 | ䷤ | 40 | ䷧ | Jiā Rén | Xiè |
| 38 | ䷥ | 39 | ䷦ | Kuí | Jiǎn |
| 51 | ䷲ | 57 | ䷸ | Zhèn | Xùn |
| 52 | ䷳ | 58 | ䷹ | Gèn | Duì |
| 53 | ䷴ | 54 | ䷵ | Jiàn | Guī Mèi |
| 55 | ䷶ | 59 | ䷺ | Fēng | Huàn |
| 56 | ䷷ | 60 | ䷻ | Lǚ | Jié |
| 61 | ䷼ | 62 | ䷽ | Zhōng Fú | Xiǎo Guò |
| 63 | ䷾ | 64 | ䷿ | Jì Jì | Wèi Jì |

## Recognised Pattern Clusters

### Boot instability / initiation cycle
**Sequence:** ䷂ (3) → ䷃ (4) → ䷄ (5)
**Pattern:** Difficulty → Youthful Folly → Waiting
**Signal:** System startup uncertainty. Progress requires patience before action.

### Bidirectional equilibrium toggle
**Sequence:** ䷊ (11) → ䷋ (12)
**Pattern:** Peace ⟷ Standstill
**Signal:** Stable states invert. Equilibrium is not permanent — it toggles.

### Decay → source → transformation pipeline
**Sequence:** ䷑ (18) → ䷯ (48) → ䷱ (50)
**Pattern:** Corruption → The Well → The Cauldron
**Signal:** System recovery: repair the source before transforming the output.

### Resource balancing pair
**Sequence:** ䷨ (41) → ䷩ (42)
**Pattern:** Decrease ⟷ Increase
**Signal:** Bounded resource oscillation. Reduction enables growth.

### Completion paradox / loop continuity
**Sequence:** ䷾ (63) → ䷿ (64)
**Pattern:** After Completion → Before Completion
**Signal:** No terminal state. Receipt appended (63) → next intent (64). Maps to NO_RECEIPT = NO_CLAIM: the loop continues.

## Pure Trigram Hexagrams (upper == lower)

| ID | Glyph | Name | Trigram | Mode |
|---|---|---|---|---|
| 1 | ䷀ | Qián | ☰ Heaven | FOCUS |
| 2 | ䷁ | Kūn | ☷ Earth | TEMPLE |
| 29 | ䷜ | Kǎn | ☵ Water | WITNESS |
| 30 | ䷝ | Lí | ☲ Fire | ORACLE |
| 51 | ䷲ | Zhèn | ☳ Thunder | FOCUS |
| 52 | ䷳ | Gèn | ☶ Mountain | WITNESS |
| 57 | ䷸ | Xùn | ☴ Wind | ORACLE |
| 58 | ䷹ | Duì | ☱ Lake | TEMPLE |

## Sequence Neighbor Binary Distance (first 20 pairs)

| Hex N | Hex N+1 | Lines differ | Note |
|---|---|---|---|
| 1 ䷀ Qián | 2 ䷁ Kūn | 6 line(s) differ | |
| 2 ䷁ Kūn | 3 ䷂ Zhūn | 2 line(s) differ | |
| 3 ䷂ Zhūn | 4 ䷃ Méng | 4 line(s) differ | |
| 4 ䷃ Méng | 5 ䷄ Xū | 4 line(s) differ | |
| 5 ䷄ Xū | 6 ䷅ Sòng | 4 line(s) differ | |
| 6 ䷅ Sòng | 7 ䷆ Shī | 3 line(s) differ | |
| 7 ䷆ Shī | 8 ䷇ Bǐ | 2 line(s) differ | |
| 8 ䷇ Bǐ | 9 ䷈ Xiǎo Chù | 4 line(s) differ | |
| 9 ䷈ Xiǎo Chù | 10 ䷉ Lǚ | 2 line(s) differ | |
| 10 ䷉ Lǚ | 11 ䷊ Tài | 4 line(s) differ | |
| 11 ䷊ Tài | 12 ䷋ Pǐ | 6 line(s) differ | |
| 12 ䷋ Pǐ | 13 ䷌ Tóng Rén | 2 line(s) differ | |
| 13 ䷌ Tóng Rén | 14 ䷍ Dà Yǒu | 2 line(s) differ | |
| 14 ䷍ Dà Yǒu | 15 ䷎ Qiān | 4 line(s) differ | |
| 15 ䷎ Qiān | 16 ䷏ Yù | 2 line(s) differ | |
| 16 ䷏ Yù | 17 ䷐ Suí | 2 line(s) differ | |
| 17 ䷐ Suí | 18 ䷑ Gǔ | 6 line(s) differ | |
| 18 ䷑ Gǔ | 19 ䷒ Lín | 3 line(s) differ | |
| 19 ䷒ Lín | 20 ䷓ Guān | 4 line(s) differ | |
| 20 ䷓ Guān | 21 ䷔ Shì Kè | 3 line(s) differ | |

## Receipt Table

| ID | Glyph | Pinyin | Upper | Lower | Mode | Tension | Binary | Yang:Yin |
|---|---|---|---|---|---|---|---|---|
| 1 | ䷀ | Qián | ☰Heaven | ☰Heaven | FOCUS | · | 111111 | 6:0 |
| 2 | ䷁ | Kūn | ☷Earth | ☷Earth | TEMPLE | · | 000000 | 0:6 |
| 3 | ䷂ | Zhūn | ☵Water | ☳Thunder | WITNESS | ⚡ | 010100 | 2:4 |
| 4 | ䷃ | Méng | ☶Mountain | ☵Water | WITNESS | · | 001010 | 2:4 |
| 5 | ䷄ | Xū | ☵Water | ☰Heaven | WITNESS | ⚡ | 010111 | 4:2 |
| 6 | ䷅ | Sòng | ☰Heaven | ☵Water | FOCUS | ⚡ | 111010 | 4:2 |
| 7 | ䷆ | Shī | ☷Earth | ☵Water | TEMPLE | ⚡ | 000010 | 1:5 |
| 8 | ䷇ | Bǐ | ☵Water | ☷Earth | WITNESS | ⚡ | 010000 | 1:5 |
| 9 | ䷈ | Xiǎo Chù | ☴Wind | ☰Heaven | ORACLE | ⚡ | 011111 | 5:1 |
| 10 | ䷉ | Lǚ | ☰Heaven | ☱Lake | FOCUS | ⚡ | 111110 | 5:1 |
| 11 | ䷊ | Tài | ☷Earth | ☰Heaven | TEMPLE | ⚡ | 000111 | 3:3 |
| 12 | ䷋ | Pǐ | ☰Heaven | ☷Earth | FOCUS | ⚡ | 111000 | 3:3 |
| 13 | ䷌ | Tóng Rén | ☰Heaven | ☲Fire | FOCUS | ⚡ | 111101 | 5:1 |
| 14 | ䷍ | Dà Yǒu | ☲Fire | ☰Heaven | ORACLE | ⚡ | 101111 | 5:1 |
| 15 | ䷎ | Qiān | ☷Earth | ☶Mountain | TEMPLE | ⚡ | 000001 | 1:5 |
| 16 | ䷏ | Yù | ☳Thunder | ☷Earth | FOCUS | ⚡ | 100000 | 1:5 |
| 17 | ䷐ | Suí | ☱Lake | ☳Thunder | TEMPLE | ⚡ | 110100 | 3:3 |
| 18 | ䷑ | Gǔ | ☶Mountain | ☴Wind | WITNESS | ⚡ | 001011 | 3:3 |
| 19 | ䷒ | Lín | ☷Earth | ☱Lake | TEMPLE | · | 000110 | 2:4 |
| 20 | ䷓ | Guān | ☴Wind | ☷Earth | ORACLE | ⚡ | 011000 | 2:4 |
| 21 | ䷔ | Shì Kè | ☲Fire | ☳Thunder | ORACLE | ⚡ | 101100 | 3:3 |
| 22 | ䷕ | Bì | ☶Mountain | ☲Fire | WITNESS | ⚡ | 001101 | 3:3 |
| 23 | ䷖ | Bō | ☶Mountain | ☷Earth | WITNESS | ⚡ | 001000 | 1:5 |
| 24 | ䷗ | Fù | ☷Earth | ☳Thunder | TEMPLE | ⚡ | 000100 | 1:5 |
| 25 | ䷘ | Wú Wàng | ☰Heaven | ☳Thunder | FOCUS | · | 111100 | 4:2 |
| 26 | ䷙ | Dà Chù | ☶Mountain | ☰Heaven | WITNESS | ⚡ | 001111 | 4:2 |
| 27 | ䷚ | Yí | ☶Mountain | ☳Thunder | WITNESS | ⚡ | 001100 | 2:4 |
| 28 | ䷛ | Dà Guò | ☱Lake | ☴Wind | TEMPLE | ⚡ | 110011 | 4:2 |
| 29 | ䷜ | Kǎn | ☵Water | ☵Water | WITNESS | · | 010010 | 2:4 |
| 30 | ䷝ | Lí | ☲Fire | ☲Fire | ORACLE | · | 101101 | 4:2 |
| 31 | ䷞ | Xián | ☱Lake | ☶Mountain | TEMPLE | ⚡ | 110001 | 3:3 |
| 32 | ䷟ | Héng | ☳Thunder | ☴Wind | FOCUS | ⚡ | 100011 | 3:3 |
| 33 | ䷠ | Dùn | ☰Heaven | ☶Mountain | FOCUS | ⚡ | 111001 | 4:2 |
| 34 | ䷡ | Dà Zhuàng | ☳Thunder | ☰Heaven | FOCUS | · | 100111 | 4:2 |
| 35 | ䷢ | Jìn | ☲Fire | ☷Earth | ORACLE | ⚡ | 101000 | 2:4 |
| 36 | ䷣ | Míng Yí | ☷Earth | ☲Fire | TEMPLE | ⚡ | 000101 | 2:4 |
| 37 | ䷤ | Jiā Rén | ☴Wind | ☲Fire | ORACLE | · | 011101 | 4:2 |
| 38 | ䷥ | Kuí | ☲Fire | ☱Lake | ORACLE | ⚡ | 101110 | 4:2 |
| 39 | ䷦ | Jiǎn | ☵Water | ☶Mountain | WITNESS | · | 010001 | 2:4 |
| 40 | ䷧ | Xiè | ☳Thunder | ☵Water | FOCUS | ⚡ | 100010 | 2:4 |
| 41 | ䷨ | Sǔn | ☶Mountain | ☱Lake | WITNESS | ⚡ | 001110 | 3:3 |
| 42 | ䷩ | Yì | ☴Wind | ☳Thunder | ORACLE | ⚡ | 011100 | 3:3 |
| 43 | ䷪ | Guài | ☱Lake | ☰Heaven | TEMPLE | ⚡ | 110111 | 5:1 |
| 44 | ䷫ | Gòu | ☰Heaven | ☴Wind | FOCUS | ⚡ | 111011 | 5:1 |
| 45 | ䷬ | Cuì | ☱Lake | ☷Earth | TEMPLE | · | 110000 | 2:4 |
| 46 | ䷭ | Shēng | ☷Earth | ☴Wind | TEMPLE | ⚡ | 000011 | 2:4 |
| 47 | ䷮ | Kùn | ☱Lake | ☵Water | TEMPLE | ⚡ | 110010 | 3:3 |
| 48 | ䷯ | Jǐng | ☵Water | ☴Wind | WITNESS | ⚡ | 010011 | 3:3 |
| 49 | ䷰ | Gé | ☱Lake | ☲Fire | TEMPLE | ⚡ | 110101 | 4:2 |
| 50 | ䷱ | Dǐng | ☲Fire | ☴Wind | ORACLE | · | 101011 | 4:2 |
| 51 | ䷲ | Zhèn | ☳Thunder | ☳Thunder | FOCUS | · | 100100 | 2:4 |
| 52 | ䷳ | Gèn | ☶Mountain | ☶Mountain | WITNESS | · | 001001 | 2:4 |
| 53 | ䷴ | Jiàn | ☴Wind | ☶Mountain | ORACLE | ⚡ | 011001 | 3:3 |
| 54 | ䷵ | Guī Mèi | ☳Thunder | ☱Lake | FOCUS | ⚡ | 100110 | 3:3 |
| 55 | ䷶ | Fēng | ☳Thunder | ☲Fire | FOCUS | ⚡ | 100101 | 3:3 |
| 56 | ䷷ | Lǚ | ☲Fire | ☶Mountain | ORACLE | ⚡ | 101001 | 3:3 |
| 57 | ䷸ | Xùn | ☴Wind | ☴Wind | ORACLE | · | 011011 | 4:2 |
| 58 | ䷹ | Duì | ☱Lake | ☱Lake | TEMPLE | · | 110110 | 4:2 |
| 59 | ䷺ | Huàn | ☴Wind | ☵Water | ORACLE | ⚡ | 011010 | 3:3 |
| 60 | ䷻ | Jié | ☵Water | ☱Lake | WITNESS | ⚡ | 010110 | 3:3 |
| 61 | ䷼ | Zhōng Fú | ☴Wind | ☱Lake | ORACLE | ⚡ | 011110 | 4:2 |
| 62 | ䷽ | Xiǎo Guò | ☳Thunder | ☶Mountain | FOCUS | ⚡ | 100001 | 2:4 |
| 63 | ䷾ | Jì Jì | ☵Water | ☲Fire | WITNESS | ⚡ | 010101 | 3:3 |
| 64 | ䷿ | Wèi Jì | ☲Fire | ☵Water | ORACLE | ⚡ | 101010 | 3:3 |

---

```
Do not decorate the water.
Clean the well.

NO_RECEIPT = NO_CLAIM
Authority: NON_SOVEREIGN
Canon: NO_SHIP
```