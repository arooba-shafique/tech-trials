"""Staff category groups shared by the academics and hr apps.

Single source of truth for the four category pills used across the dashboard
(Management Staff, Administration, Janitorial, Teacher) and for the
category-based Provident Fund criteria.
"""

STAFF_CATEGORY_ORDER = ('management_staff', 'administration', 'janitorial', 'teacher')

STAFF_CATEGORY_DESIGNATIONS = {
    'management_staff': {'director', 'manager_academics', 'hr_manager', 'assistant_manager_academics'},
    'administration': {'vp', 'coordinator', 'team_lead', 'accountant', 'fdc'},
    'janitorial': {'aya', 'photocopier', 'office_boy', 'sweeper', 'compositer'},
    'teacher': {'teacher'},
}

# Designations that belong to a category for salary/PF purposes but are NOT part
# of the staff-table ordering groups (adding them there would change row order).
PF_EXTRA_DESIGNATIONS = {
    'management_staff': {'manager', 'group_head', 'section_head', 'assistant_manager'},
    'administration': {'a_coordinator'},
}

# Provident Fund criteria (% of basic) per category.
DEFAULT_PF_PCT = {
    'management_staff': 5,
    'administration': 5,
    'janitorial': 0,
    'teacher': 7.5,
}

_DESIGNATION_RANK = {
    designation: rank
    for rank, category in enumerate(STAFF_CATEGORY_ORDER)
    for designation in STAFF_CATEGORY_DESIGNATIONS[category]
}

PF_CATEGORY_DESIGNATIONS = {
    category: set(designations)
    for category, designations in STAFF_CATEGORY_DESIGNATIONS.items()
}
for _category, _designations in PF_EXTRA_DESIGNATIONS.items():
    PF_CATEGORY_DESIGNATIONS[_category] |= _designations

_DESIGNATION_PF_CATEGORY = {
    designation: category
    for category, designations in PF_CATEGORY_DESIGNATIONS.items()
    for designation in designations
}


def staff_category(designation):
    """Return the ordering category for a designation, or None if ungrouped."""
    key = (designation or '').strip().lower()
    if not key:
        return None
    for category in STAFF_CATEGORY_ORDER:
        if key in STAFF_CATEGORY_DESIGNATIONS[category]:
            return category
    return None


def pf_category(designation):
    """Return the Provident Fund category for a designation.

    Falls back to management_staff for designations outside every known group,
    and to teacher when the designation is blank (model default is 'teacher').
    """
    key = (designation or '').strip().lower()
    if not key:
        return 'teacher'
    return _DESIGNATION_PF_CATEGORY.get(key, 'management_staff')


def default_pf_pct(designation):
    return DEFAULT_PF_PCT[pf_category(designation)]


def staff_order_key(item):
    """Order like the Staff table: category (Management → Administration →
    Janitorial → Teacher) first, then Employee ID numerically within each."""
    employee = getattr(item, 'employee', None)
    designation = (getattr(employee, 'designation', None) or '').strip().lower()
    rank = _DESIGNATION_RANK.get(designation, len(STAFF_CATEGORY_ORDER))
    employee_id = (getattr(employee, 'employee_id', None) or '')
    digits = ''.join(ch for ch in employee_id if ch.isdigit())
    return (rank, int(digits) if digits else 0, employee_id.lower())
