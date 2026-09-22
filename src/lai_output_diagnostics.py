"""Value-free output diagnostics; never used to accept output or select retries."""

TOP_FIELDS = ('belief_status', 'confidence', 'explanation', 'evidence_summary')
EVIDENCE_FIELDS = ('supporting_evidence', 'contradicting_evidence')
TYPES = ('object', 'array', 'string', 'boolean', 'number', 'null', 'other', 'missing')
CATEGORIES = ('invalid_json', 'response_envelope', 'top_level_type', 'missing_fields',
              'schema_mismatch', 'field_type_mismatch', 'field_value_invalid',
              'evidence_structure_mismatch', 'item_type_mismatch', 'evidence_item_limit',
              'no_shape_error_detected')


def _type(value):
    if value is None: return 'null'
    if isinstance(value, bool): return 'boolean'
    if isinstance(value, (int, float)): return 'number'
    if isinstance(value, str): return 'string'
    if isinstance(value, dict): return 'object'
    if isinstance(value, list): return 'array'
    return 'other'


def output_diagnostics(value=None, *, parsed=None, category=None):
    """Unknown key names are redacted: model-controlled keys can contain secrets."""
    top = value if parsed and isinstance(value, dict) else {}
    evidence = top.get('evidence_summary')
    summary = evidence if isinstance(evidence, dict) else {}
    def keys(mapping, allowed):
        return sorted(k for k in allowed if k in mapping) + (
            ['<redacted_unknown_key>'] if any(k not in allowed for k in mapping) else [])
    result = {
        'json_parse_success': parsed,
        'top_level_type': _type(value) if parsed else None,
        'top_level_keys': keys(top, TOP_FIELDS) if parsed and isinstance(value, dict) else None,
        'evidence_summary_keys': keys(summary, EVIDENCE_FIELDS) if isinstance(evidence, dict) else None,
        'field_presence': {k: k in top for k in TOP_FIELDS},
        'field_types': {k: _type(top[k]) if k in top else 'missing' for k in TOP_FIELDS},
        'evidence_field_presence': {k: k in summary for k in EVIDENCE_FIELDS},
        'evidence_field_types': {k: _type(summary[k]) if k in summary else 'missing' for k in EVIDENCE_FIELDS},
        'evidence_item_types': {k: sorted({_type(v) for v in summary[k]}) if isinstance(summary.get(k), list) else None for k in EVIDENCE_FIELDS},
        'evidence_item_counts': {k: len(summary[k]) if isinstance(summary.get(k), list) else None for k in EVIDENCE_FIELDS},
    }
    if category is None:
        if not isinstance(value, dict): category = 'top_level_type'
        elif set(TOP_FIELDS) - set(top): category = 'missing_fields'
        elif set(top) != set(TOP_FIELDS): category = 'schema_mismatch'
        elif any(result['field_types'][k] != t for k, t in [('belief_status','string'),('confidence','number'),('explanation','string')]): category = 'field_type_mismatch'
        elif top['belief_status'] not in ('VALID','UNCERTAIN','INVALID') or not 0 <= top['confidence'] <= 1: category = 'field_value_invalid'
        elif not isinstance(evidence, dict) or set(summary) != set(EVIDENCE_FIELDS) or any(not isinstance(summary[k], list) for k in EVIDENCE_FIELDS): category = 'evidence_structure_mismatch'
        elif any(len(summary[k]) > 3 for k in EVIDENCE_FIELDS): category = 'evidence_item_limit'
        elif any(not isinstance(v, str) for k in EVIDENCE_FIELDS for v in summary[k]): category = 'item_type_mismatch'
        else: category = 'no_shape_error_detected'
    result['validation_category'] = category
    return result


def safe_diagnostics(value):
    """Project only known metadata fields and fixed vocabulary before persistence."""
    if not isinstance(value, dict) or "json_parse_success" not in value: return None
    result = {}
    for key in ('json_parse_success',):
        result[key] = value.get(key) if type(value.get(key)) is bool else None
    result['validation_category'] = value.get('validation_category') if value.get('validation_category') in CATEGORIES else None
    result['top_level_type'] = value.get('top_level_type') if value.get('top_level_type') in TYPES else None
    for key, fields in [('top_level_keys',TOP_FIELDS), ('evidence_summary_keys',EVIDENCE_FIELDS)]:
        items = value.get(key)
        result[key] = ([item for item in fields if item in items] +
                       (['<redacted_unknown_key>'] if any(item not in fields for item in items) else [])) if isinstance(items,list) else None
    for key, fields in [('field_presence',TOP_FIELDS),('evidence_field_presence',EVIDENCE_FIELDS),
                        ('field_types',TOP_FIELDS),('evidence_field_types',EVIDENCE_FIELDS),
                        ('evidence_item_types',EVIDENCE_FIELDS),('evidence_item_counts',EVIDENCE_FIELDS)]:
        items = value.get(key)
        if not isinstance(items,dict): continue
        result[key] = {}
        for field in fields:
            item = items.get(field)
            if key.endswith('presence'): safe = item if type(item) is bool else None
            elif key == 'evidence_item_counts': safe = item if type(item) is int and item >= 0 else None
            elif key == 'evidence_item_types': safe = sorted(t for t in TYPES if t in item) if isinstance(item,list) else None
            else: safe = item if item in TYPES else None
            result[key][field] = safe
    return result
