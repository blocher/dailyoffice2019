"""
Psalm Reference Converter
=========================

This module provides functionality to convert Psalm and Verse references between
different Bible translations and traditions. It handles the complex numbering differences
between the Masoretic Text (Hebrew) and the Septuagint (Greek/Vulgate), as well as
versification differences regarding Psalm titles (superscriptions).

Supported Traditions:
---------------------
1. Masoretic (MT): Used by Jewish and most Protestant traditions.
   - Numbering: 1-150.
   - Splits: Ps 9 & 10 are separate; Ps 114 & 115 are separate.
2. Septuagint (LXX): Used by Orthodox and Catholic (Vulgate/Douay) traditions.
   - Numbering: 1-150 (but offset).
   - Merges: Ps 9+10 -> Ps 9; Ps 114+115 -> Ps 113.
   - Splits: Ps 116 -> Ps 114+115; Ps 147 -> Ps 146+147.

Versification Styles:
---------------------
1. KJV-Style: Psalm titles are NOT numbered as verses. Verse 1 is the first line of the poem.
2. MT-Style: Psalm titles ARE numbered as verse 1 (and sometimes 2).

Usage:
------
    from psalm_converter import convert_psalm_reference

    # Convert Psalm 23:1 from KJV to Septuagint
    start_p, end_p, start_v, end_v = convert_psalm_reference(
        23, 23, 1, 1, 'King James Version', 'Septuagint'
    )
"""

# ==========================================
# Data: Translation Configuration
# ==========================================

TRANSLATIONS = {
    # --- Masoretic Numbering / KJV Versification (No Title Verses) ---
    'King James Version': {'system': 'MT', 'versification': 'KJV'},
    'Authorized Version': {'system': 'MT', 'versification': 'KJV'}, # Alias
    'English Standard Version': {'system': 'MT', 'versification': 'KJV'},
    'Revised Standard Version': {'system': 'MT', 'versification': 'KJV'},
    'Revised Standard Version (2nd Catholic Edition)': {'system': 'MT', 'versification': 'KJV'}, # RSV-2CE usually follows RSV numbering
    'New American Standard Bible': {'system': 'MT', 'versification': 'KJV'},
    'New American Standard Bible Revised Edition': {'system': 'MT', 'versification': 'KJV'},
    'Nueva Version International': {'system': 'MT', 'versification': 'KJV'},
    'New Revised Standard Version': {'system': 'MT', 'versification': 'KJV'},
    'New Revised Standard Version Updated Edition': {'system': 'MT', 'versification': 'KJV'},
    'Book of Common Prayer (1979)': {'system': 'MT', 'versification': 'KJV'},
    'Coverdale Psalter': {'system': 'MT', 'versification': 'KJV'}, # Traditional BCP
    'New Coverdale Psalter': {'system': 'MT', 'versification': 'KJV'}, # BCP 2019
    'Jerusalem Bible': {'system': 'MT', 'versification': 'KJV'}, # English JB uses MT numbering
    'Grail Psalter (1963)': {'system': 'MT', 'versification': 'KJV'}, 
    'Grail Psalter (1993)': {'system': 'MT', 'versification': 'KJV'},
    'Abbey Psalms and Canticles (2020)': {'system': 'MT', 'versification': 'KJV'},

    # --- Masoretic Numbering / MT Versification (Titles ARE Verses) ---
    'Masoretic Text': {'system': 'MT', 'versification': 'MT'},
    'New American Bible, Revised Edition': {'system': 'MT', 'versification': 'MT'}, # NABRE counts titles
    'Nova Vulgata (1979) (Second Typical Edition)': {'system': 'MT', 'versification': 'MT'}, # Nova Vulgata uses MT numbering

    # --- Septuagint Numbering / LXX Versification (Usually Titles Counted or similar to MT in ancient texts, but mapped here) ---
    'Septuaginet': {'system': 'LXX', 'versification': 'LXX'}, # Typo handling
    'Septuagint': {'system': 'LXX', 'versification': 'LXX'},
    'Vulgate (Council of Trent, 1546)': {'system': 'LXX', 'versification': 'LXX'},
    'Vulgate (Clementine / Sixto-Clementine Vulgate (1592))': {'system': 'LXX', 'versification': 'LXX'},
    'Douay-Rheims Bible': {'system': 'LXX', 'versification': 'KJV'}, # DR usually does NOT number titles as v1 in English editions? Checking...
                                                                      # DR: "Unto the end, a psalm for David..." is usually text, but numbering starts at 1 for "When I called...".
                                                                      # So DR is effectively KJV-style versification despite being LXX system.
                                                                      # We'll tag it KJV for safety in English.
}

# ==========================================
# Data: Mappings
# ==========================================

# Map MT Psalm Number -> LXX Psalm Number(s)
# 1:1 unless specified
MT_TO_LXX_MAP = {
    # 9 and 10 merge
    9: 9, 
    10: 9, 
    # 11-113: Shift by -1
    # 114 and 115 merge
    114: 113,
    115: 113,
    # 116 splits
    116: (114, 115),
    # 117-146: Shift by -1
    # 147 splits
    147: (146, 147),
}

# Generate numeric shifts
for i in range(11, 114):
    MT_TO_LXX_MAP[i] = i - 1
for i in range(117, 147):
    MT_TO_LXX_MAP[i] = i - 1

# Reverse Map (LXX -> MT)
LXX_TO_MT_MAP = {}
for mt, lxx in MT_TO_LXX_MAP.items():
    if isinstance(lxx, int):
        if lxx not in LXX_TO_MT_MAP:
            LXX_TO_MT_MAP[lxx] = mt
        else:
            # Merge detected
            if isinstance(LXX_TO_MT_MAP[lxx], int):
                LXX_TO_MT_MAP[lxx] = (LXX_TO_MT_MAP[lxx], mt)
            else:
                LXX_TO_MT_MAP[lxx] += (mt,)
    elif isinstance(lxx, tuple):
        for part in lxx:
            LXX_TO_MT_MAP[part] = mt

# MT Title Offsets (Number of verses to subtract to get KJV numbering)
# Default is 0.
MT_TITLE_OFFSETS = {}
# Populate with Psalms that have titles (approximate list for standard MT)
# Heuristic: Most have 1 verse title. Some have 2. Orphans have 0.
_HAS_TITLE_OFFSET_1 = [
    3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 
    26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 
    48, 49, 50, 53, 55, 56, 57, 58, 59, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 72, 
    73, 74, 75, 76, 77, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 92, 98, 100, 
    101, 102, 103, 108, 109, 110, 138, 139, 140, 141, 142, 143, 144, 145
]
_HAS_TITLE_OFFSET_2 = [51, 52, 54, 60]

for p in _HAS_TITLE_OFFSET_1:
    MT_TITLE_OFFSETS[p] = 1
for p in _HAS_TITLE_OFFSET_2:
    MT_TITLE_OFFSETS[p] = 2


# ==========================================
# Logic
# ==========================================

def get_translation_config(translation_name):
    """Normalize translation name and return config."""
    # Handle minor variations or exact matches
    name = translation_name.strip()
    if name in TRANSLATIONS:
        return TRANSLATIONS[name]
    
    # Try case insensitive
    for k, v in TRANSLATIONS.items():
        if k.lower() == name.lower():
            return v

    raise ValueError(f"Unsupported translation: {translation_name}")

def _normalize_to_pivot(psalm, verse, system, versification):
    """
    Convert (System, Verse) -> (MT_Psalm, KJV_Verse_Index).
    KJV_Verse_Index: 1-based index of the *Text* (ignoring titles).
    """
    
    p_mt = psalm
    v_kjv = verse
    
    # 1. System Conversion (LXX -> MT)
    if system == 'LXX':
        if psalm in LXX_TO_MT_MAP:
            val = LXX_TO_MT_MAP[psalm]
            
            # Simple 1:1 map
            if isinstance(val, int):
                p_mt = val
                
            # Merge Case (LXX 9 -> MT 9, 10; LXX 113 -> MT 114, 115)
            elif isinstance(val, tuple):
                # We need to determine WHICH MT psalm it maps to based on verse.
                # Assuming KJV-like versification for cutoff logic for now, 
                # or approximating based on standard lengths.
                
                if psalm == 9:
                    # LXX 9 is approx 38 verses.
                    # MT 9 is 20 verses. MT 10 is 18 verses.
                    # If verse <= 20: MT 9. Else: MT 10.
                    if verse <= 20:
                        p_mt = 9
                        v_kjv = verse
                    else:
                        p_mt = 10
                        v_kjv = verse - 20
                elif psalm == 113:
                    # LXX 113 -> MT 114 (8 verses) + MT 115 (18 verses)
                    if verse <= 8:
                        p_mt = 114
                        v_kjv = verse
                    else:
                        p_mt = 115
                        v_kjv = verse - 8
        
        # Split Case (LXX 114, 115 -> MT 116; LXX 146, 147 -> MT 147)
        # Note: LXX_TO_MT_MAP only maps keys present. 
        # But wait, logic above says MT_TO_LXX[116] = (114, 115).
        # So LXX 114 and 115 keys are NOT in LXX_TO_MT_MAP? 
        # Let's check how LXX_TO_MT_MAP is built.
        # It iterates MT_TO_LXX. 
        # If MT 116 -> (114, 115), then LXX_TO_MT[114] = 116 and LXX_TO_MT[115] = 116.
        # So they ARE in the map as integers.
        
        # But we need to adjust Verse numbers for the "Second Part" of the split.
        if p_mt == 116:
            # If input was LXX 114: No change needed (starts at 1).
            # If input was LXX 115: It starts at MT 116:10.
            if psalm == 115:
                v_kjv = verse + 9
        elif p_mt == 147:
            # If input was LXX 146: No change.
            # If input was LXX 147: It starts at MT 147:12.
            if psalm == 147:
                v_kjv = verse + 11

    # 2. Versification Conversion (Title Offset)
    # At this point, p_mt is the MT Psalm number.
    # v_kjv is the verse number *assuming the input system's title logic*.
    # If input is MT-Versification (Titles Counted), we must subtract offset to get KJV-Index.
    # If input is KJV-Versification, offset is 0.
    
    offset = 0
    if versification == 'MT': 
        offset = MT_TITLE_OFFSETS.get(p_mt, 0)
    elif versification == 'LXX':
        # If LXX system uses titles as verses, we should subtract.
        # Assuming for now 'LXX' config implies title counting similar to MT.
        offset = MT_TITLE_OFFSETS.get(p_mt, 0)
        
    v_norm = v_kjv - offset
    
    return p_mt, v_norm

def _denormalize_from_pivot(p_mt, v_norm, system, versification):
    """
    Convert (MT_Psalm, KJV_Verse_Index) -> (Output_System_Psalm, Output_Verse).
    """
    
    p_out = p_mt
    v_out = v_norm
    
    # 1. System Conversion (MT -> LXX)
    if system == 'LXX':
        # Check MT -> LXX Map
        if p_mt in MT_TO_LXX_MAP:
            val = MT_TO_LXX_MAP[p_mt]
            
            if isinstance(val, int):
                p_out = val
                # Check for Merge Targets (MT 10 -> LXX 9; MT 115 -> LXX 113)
                if p_mt == 10:
                    # MT 10:1 -> LXX 9:21
                    # We need to add MT 9's length (20).
                    v_out = v_norm + 20
                elif p_mt == 115:
                    # MT 115:1 -> LXX 113:9
                    v_out = v_norm + 8
                    
            elif isinstance(val, tuple):
                # Split Case (MT 116 -> LXX 114, 115)
                part1, part2 = val
                
                if p_mt == 116:
                    # Cutoff is 9.
                    if v_norm <= 9:
                        p_out = part1 # 114
                        v_out = v_norm
                    else:
                        p_out = part2 # 115
                        v_out = v_norm - 9
                elif p_mt == 147:
                    # Cutoff is 11.
                    if v_norm <= 11:
                        p_out = part1 # 146
                        v_out = v_norm
                    else:
                        p_out = part2 # 147
                        v_out = v_norm - 11

    # 2. Versification Conversion (Add Offset)
    # We now have the correct Psalm Number for the output system.
    # But we need to know the offset for THAT psalm.
    # Wait, the offset map is keyed by MT Psalm Number. 
    # If we are in LXX system, does the offset logic still apply to the *LXX* psalm number?
    # Usually, if titles are counted, they are counted.
    # If we are outputting to 'LXX' versification, we should apply the offset corresponding to the content.
    
    # Simplified assumption: Use the MT offset of the *source* content if meaningful, 
    # or look up offset for the resulting psalm if possible. 
    # But offsets are structural.
    # Let's use the MT Psalm number to look up the structural offset (does it have a title?).
    # If mapped 1:1, use MT offset.
    # If merged/split:
    #   - MT 116 -> LXX 114, 115. MT 116 has offset 0 (Orphan). So 0.
    #   - MT 9 -> LXX 9. MT 9 has offset 1.
    #   - MT 10 -> LXX 9. MT 10 has offset 0. 
    #     So LXX 9 starts with title (from MT 9). 
    #     If we are in the MT 10 part of LXX 9 (v21+), do we add offset?
    #     LXX 9:1 is Title. LXX 9:21 is MT 10:1.
    #     If v_norm (KJV index) is 1 (MT 10:1), and we map to LXX 9, 
    #     v_out became 21 (from merge logic).
    #     If we apply offset of MT 9 (1), result is 22.
    #     Does LXX 9:22 correspond to MT 10:1? 
    #     LXX 9:1 (Title). LXX 9:2 (MT 9:1). ... LXX 9:21 (MT 9:20). LXX 9:22 (MT 10:1).
    #     Yes. So we apply the offset of the *Head* of the merged psalm.
    
    # Logic: Get the MT equivalent of the HEAD of the output psalm to determine offset.
    # If p_out (LXX) came from MT X, Y... use X's offset.
    
    # Find effective MT source for offset lookup
    mt_source_for_offset = p_mt
    if system == 'LXX':
        # If we are in LXX system, p_out is LXX number.
        # We need to know if this LXX psalm *starts* with a title.
        # Reverse lookup:
        if p_out in LXX_TO_MT_MAP:
            src = LXX_TO_MT_MAP[p_out]
            if isinstance(src, tuple):
                mt_source_for_offset = src[0] # Use the first part
            else:
                mt_source_for_offset = src
    
    final_offset = 0
    if versification == 'MT' or versification == 'LXX':
        final_offset = MT_TITLE_OFFSETS.get(mt_source_for_offset, 0)
    
    v_final = v_out + final_offset
    
    # Safety: If verse <= 0 (e.g. title requested in KJV), clamp to 1 or handle?
    # User just asked for conversion. If valid input title -> output no title, 
    # v_final might be 0. 
    # We will return max(1, v_final) to ensure valid reference, 
    # effectively mapping Title to Verse 1 if titles aren't supported.
    if v_final < 1:
        v_final = 1
        
    return p_out, v_final

def convert_psalm_reference(start_psalm, end_psalm, start_verse, end_verse, translation_in, translation_out):
    """
    Convert a range of verses from one translation to another.
    """
    conf_in = get_translation_config(translation_in)
    conf_out = get_translation_config(translation_out)
    
    # Normalize Start
    p_mt_start, v_norm_start = _normalize_to_pivot(
        start_psalm, start_verse, conf_in['system'], conf_in['versification']
    )
    
    # Normalize End
    p_mt_end, v_norm_end = _normalize_to_pivot(
        end_psalm, end_verse, conf_in['system'], conf_in['versification']
    )
    
    # Denormalize Start
    p_out_start, v_out_start = _denormalize_from_pivot(
        p_mt_start, v_norm_start, conf_out['system'], conf_out['versification']
    )
    
    # Denormalize End
    p_out_end, v_out_end = _denormalize_from_pivot(
        p_mt_end, v_norm_end, conf_out['system'], conf_out['versification']
    )
    
    return p_out_start, p_out_end, v_out_start, v_out_end

if __name__ == "__main__":
    # Test Suite
    print("Running Tests...")
    
    # 1. Standard Case (Ps 23)
    # MT 23:1 (Title) -> KJV 23:? (KJV doesn't have titles, assumes map to v1?)
    # MT 23:2 (Text) -> KJV 23:1
    print(f"MT 23:1-6 -> KJV: {convert_psalm_reference(23, 23, 1, 6, 'Masoretic Text', 'King James Version')}") 
    # Expected: 23, 23, 1, 5 (Since MT 1 is title (offset 1), MT 2 is KJV 1. MT 6 is KJV 5)
    
    # 2. Split Case (Ps 116)
    # MT 116:1 -> LXX 114:1
    # MT 116:10 -> LXX 115:1
    print(f"MT 116:1-19 -> LXX: {convert_psalm_reference(116, 116, 1, 19, 'Masoretic Text', 'Septuagint')}")
    # Note: This simply converts start and end points.
    # Start: MT 116:1 -> LXX 114:1
    # End: MT 116:19 -> LXX 115:10
    # Result should describe the span in the OUTPUT system.
    # (114, 115, 1, 10)
    
    # 3. Merge Case (Ps 9-10)
    # MT 10:1 -> LXX 9:22 (Approx, depends on offset of Ps 9)
    # MT 10 is orphan (offset 0). MT 9 has title (offset 1).
    # LXX 9 inherits title.
    # MT 10:1 (Text) -> Norm: 10, 1.
    # Denorm: LXX 9. Norm 1 -> +20 -> 21. +Offset(1) -> 22.
    print(f"MT 10:1 -> LXX: {convert_psalm_reference(10, 10, 1, 1, 'Masoretic Text', 'Septuagint')}")

    # 4. Douay-Rheims (LXX System, KJV Verses/No Titles?)
    # Let's assume DR doesn't count titles.
    # MT 23:1 (Title) -> DR 22:?
    print(f"MT 23:1 -> DR: {convert_psalm_reference(23, 23, 1, 1, 'Masoretic Text', 'Douay-Rheims Bible')}")
    
    # 5. Reverse: LXX 113 -> MT 114/115
    print(f"LXX 113:1 -> MT: {convert_psalm_reference(113, 113, 1, 1, 'Septuagint', 'Masoretic Text')}")
    # LXX 113:9 -> MT 115:1
    print(f"LXX 113:9 -> MT: {convert_psalm_reference(113, 113, 9, 9, 'Septuagint', 'Masoretic Text')}")
