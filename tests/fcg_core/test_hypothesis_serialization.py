"""Property-based serialization tests."""

from hypothesis import given, strategies as st

from fcg_core.canonical_v2 import canonical_hash_v2


_JCS_INT_MAX = 9007199254740991
_JCS_INT_MIN = -9007199254740991


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=8),
        st.integers(min_value=_JCS_INT_MIN, max_value=_JCS_INT_MAX),
        max_size=10,
    )
)
def test_canonical_hash_stable_under_key_reorder(d: dict):
    items = list(d.items())
    d1 = dict(items)
    d2 = dict(reversed(items))
    assert canonical_hash_v2(d1) == canonical_hash_v2(d2)
