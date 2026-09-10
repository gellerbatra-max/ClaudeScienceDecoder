"""accumark_errors.py - the v2 exception taxonomy for every ZIP/object entry
point in accumark_pds.py and accumark_marker.py.

All decode failures a caller should expect to handle raise one of these
instead of a bare IndexError/struct.error/SystemExit. AccuMarkError itself
subclasses ValueError (not Exception) so existing `except ValueError` call
sites - including accumark_pds.decode's own block loop - keep working
unchanged across the v1 -> v2 upgrade; see CHANGELOG.md.

    AccuMarkError(ValueError)
     |- NotAnAccuMarkZip        no XGGT member found in the container
     |   `- NestedArchive       ...but it holds zip(s): named in .nested
     |- ObjectError
     |   |- NotAnAccuMarkObject   magic missing
     |   |- TruncatedObject       declared length exceeds bytes present
     |   `- WrongObjectType       type u16 is not the one requested
     |- NoSuchObject             no marker / no piece / no <kind> in the zip
     |- AmbiguousObject          duplicate members, or N candidates where 1 expected
     `- DecodeError              a block/section failed to parse
"""


class AccuMarkError(ValueError):
    """Base for every controlled v2 decode failure. Subclasses ValueError so
    v1 callers written against `except ValueError` are unaffected."""

    def __init__(self, message, source=None):
        self.source = source
        super().__init__(f'{message} ({source})' if source else message)


class NotAnAccuMarkZip(AccuMarkError):
    """The container opened fine as a ZIP, but no member starts with the
    AccuMark IXPORT magic."""


class NestedArchive(NotAnAccuMarkZip):
    """No AccuMark object at the top level, but the container holds one or
    more nested ZIPs - e.g. a Google-Drive download wrapper, or a hand-built
    zip of drawn DXFs plus the real export. Not auto-descended (v2 design
    decision: nested zips are rejected with a clear pointer, not silently
    unwrapped)."""

    def __init__(self, message, source=None, nested=()):
        self.nested = list(nested)
        if self.nested:
            names = ', '.join(repr(n) for n in self.nested)
            message = f'{message}; found {len(self.nested)} nested ZIP(s): {names}. Extract it first.'
        super().__init__(message, source)


class ObjectError(AccuMarkError):
    """Base for a single malformed XGGT object."""


class NotAnAccuMarkObject(ObjectError):
    """The 18-byte magic is missing."""


class TruncatedObject(ObjectError):
    """The object's own declared length (header payload_len, or a section
    directory offset) exceeds the bytes actually present."""

    def __init__(self, message, source=None, declared=None, actual=None):
        self.declared = declared
        self.actual = actual
        if declared is not None and actual is not None:
            message = f'{message} (declared {declared} bytes, have {actual})'
        super().__init__(message, source)


class WrongObjectType(ObjectError):
    """The object's type code is not the one the caller asked for."""

    def __init__(self, message, source=None, got=None, want=None):
        self.got, self.want = got, want
        super().__init__(message, source)


class NoSuchObject(AccuMarkError):
    """The zip is a valid AccuMark export but has none of the object kind
    requested (no marker, no piece, no order, ...)."""


class AmbiguousObject(AccuMarkError):
    """More than one candidate object exists where exactly one was expected -
    duplicate member names, or several pieces where the caller asked for
    "the" piece. Disambiguate with an explicit member= argument."""

    def __init__(self, message, source=None, candidates=()):
        self.candidates = list(candidates)
        if self.candidates:
            names = ', '.join(repr(n) for n in self.candidates)
            message = f'{message}: {names}'
        super().__init__(message, source)


class DecodeError(AccuMarkError):
    """A block or section within an otherwise valid object failed to parse."""


class NotADxf(AccuMarkError):
    """A path handed to a DXF reader (verify_capture.dxf_outline,
    verify_marker.dxf_marker) shows no evidence of being a DXF - no group-code
    pair line starting a SECTION, and no $ACADVER header variable. Distinguishes
    "not a DXF at all" from "a real DXF that happens to contain zero loops"."""
