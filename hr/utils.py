"""Small helpers for the HR module."""

_ONES = [
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen',
]
_TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']


def _under_thousand(n):
    """1..999 -> words."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return _TENS[t] + (' ' + _ONES[o] if o else '')
    h, r = divmod(n, 100)
    words = _ONES[h] + ' hundred'
    if r:
        words += ' and ' + _under_thousand(r)
    return words


def number_to_words(amount):
    """PKR amount -> words in the Pakistani lakh/crore system.

    607807 -> 'Six lac seven thousand eight hundred and seven'
    """
    n = int(amount)
    if n <= 0:
        return 'Zero'
    parts = []
    crore, n = divmod(n, 10 ** 7)
    lac, n = divmod(n, 10 ** 5)
    thousand, n = divmod(n, 1000)
    hundred, n = divmod(n, 100)
    if crore:
        parts.append(_under_thousand(crore) + ' crore')
    if lac:
        parts.append(_under_thousand(lac) + ' lac')
    if thousand:
        parts.append(_under_thousand(thousand) + ' thousand')
    if hundred:
        parts.append(_under_thousand(hundred) + ' hundred')
    if n:
        if parts:
            parts.append('and')
        parts.append(_under_thousand(n))
    words = ' '.join(parts)
    # Sentence case: "Six lac seven thousand eight hundred and seven"
    return words[:1].upper() + words[1:].lower()


def ordinal(day):
    """1 -> '1st', 2 -> '2nd', 11 -> '11th', 14 -> '14th'."""
    day = int(day)
    if 10 < day % 100 < 14:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f'{day}{suffix}'
