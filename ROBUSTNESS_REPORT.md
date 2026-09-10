# Robustness report (v2)
decoder_version: accumark_pds=2.0 accumark_marker=2.0

303 cases, 249 passed, 54 failed, 6.1s

## Supported

- ZIP structural variants (Oracle A, 126/126): STORED/DEFLATED/BZIP2/LZMA and mixed compression, reversed/shuffled member order, folder prefixes, deep nesting, backslash paths, directory entries, extra junk members, non-ASCII/long names, `.TMP`/`.dat` renamed members, dropped `ver.5`/`comments.txt`, missing/replaced archive comment, zeroed timestamps - decode identically to the original on every seed.
- Malformed-input contract (Oracle B, 12/12): every case below raises a named `accumark_errors.AccuMarkError` subclass (or `zipfile.BadZipFile` for a non-ZIP container) - never `SystemExit`, never a bare `IndexError`/`struct.error`, never a silent wrong answer.

## Oracle A (126/126 ok)

| case | seed | verdict | detail |
|---|---|---|---|
| CAP-C00-BASE/v_stored | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_deflated | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_bzip2 | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_lzma | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_mixed_compression | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_reversed_order | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_shuffled_order | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_folder_prefix | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_deep_nesting | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_backslash_paths | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_directory_entries | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_extra_junk | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_nonascii_name | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_long_name | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_upper_tmp | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_renamed_ext | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_drop_ver5 | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_drop_comments | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_no_comment | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_replaced_comment | CAP-C00-BASE | ok | ok |
| CAP-C00-BASE/v_zeroed_timestamps | CAP-C00-BASE | ok | ok |
| CAP-C62-DART/v_stored | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_deflated | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_bzip2 | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_lzma | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_mixed_compression | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_reversed_order | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_shuffled_order | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_folder_prefix | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_deep_nesting | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_backslash_paths | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_directory_entries | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_extra_junk | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_nonascii_name | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_long_name | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_upper_tmp | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_renamed_ext | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_drop_ver5 | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_drop_comments | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_no_comment | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_replaced_comment | CAP-C62-DART | ok | ok |
| CAP-C62-DART/v_zeroed_timestamps | CAP-C62-DART | ok | ok |
| CLAUDE-GRADE-MARKER/v_stored | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_deflated | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_bzip2 | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_lzma | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_mixed_compression | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_reversed_order | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_shuffled_order | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_folder_prefix | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_deep_nesting | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_backslash_paths | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_directory_entries | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_extra_junk | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_nonascii_name | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_long_name | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_upper_tmp | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_renamed_ext | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_drop_ver5 | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_drop_comments | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_no_comment | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_replaced_comment | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/v_zeroed_timestamps | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_stored | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_deflated | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_bzip2 | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_lzma | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_mixed_compression | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_reversed_order | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_shuffled_order | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_folder_prefix | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_deep_nesting | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_backslash_paths | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_directory_entries | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_extra_junk | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_nonascii_name | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_long_name | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_upper_tmp | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_renamed_ext | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_drop_ver5 | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_drop_comments | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_no_comment | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_replaced_comment | CLAUDE-GRADE-MARKER | ok | ok |
| CLAUDE-GRADE-MARKER/place_marker/v_zeroed_timestamps | CLAUDE-GRADE-MARKER | ok | ok |
| 2303-BD137-PLACED/v_stored | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_deflated | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_bzip2 | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_lzma | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_mixed_compression | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_reversed_order | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_shuffled_order | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_folder_prefix | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_deep_nesting | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_backslash_paths | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_directory_entries | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_extra_junk | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_nonascii_name | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_long_name | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_upper_tmp | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_renamed_ext | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_drop_ver5 | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_drop_comments | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_no_comment | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_replaced_comment | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/v_zeroed_timestamps | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_stored | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_deflated | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_bzip2 | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_lzma | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_mixed_compression | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_reversed_order | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_shuffled_order | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_folder_prefix | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_deep_nesting | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_backslash_paths | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_directory_entries | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_extra_junk | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_nonascii_name | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_long_name | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_upper_tmp | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_renamed_ext | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_drop_ver5 | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_drop_comments | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_no_comment | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_replaced_comment | 2303-BD137-PLACED | ok | ok |
| 2303-BD137-PLACED/place_marker/v_zeroed_timestamps | 2303-BD137-PLACED | ok | ok |

## Oracle B (12/12 ok)

| case | seed | verdict | detail |
|---|---|---|---|
| empty_file | - | ok | ok (BadZipFile) |
| random_bytes | - | ok | ok (BadZipFile) |
| truncated_50pct | CAP-C00-BASE | ok | ok (BadZipFile) |
| zero_members | - | ok | ok (NotAnAccuMarkZip) |
| only_junk_members | - | ok | ok (NotAnAccuMarkZip) |
| marker_zip_to_decode_zip | 2303-BD137-PLACED | ok | ok (AmbiguousObject) |
| order_only_to_decode_zip | COSTORDER | ok | ok (NoSuchObject) |
| duplicate_members | CAP-C00-BASE | ok | ok (no exception, as required) |
| nested_wrapper_zip | Drive-wrapper | ok | ok (NestedArchive) |
| truncated_object_123B_decode_zip | CAP-C00-BASE | ok | ok (NoSuchObject) |
| truncated_object_123B_list_zip | CAP-C00-BASE | ok | ok (no exception, as required) |
| truncated_object_200B_list_zip | 2303-BD137-PLACED | ok | ok (no exception, as required) |

## Oracle C (111/165 ok)

| case | seed | verdict | detail |
|---|---|---|---|
| CAP-C00-BASE/off=0x3de/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3de/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3de/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x288/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x288/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x288/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x297/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x297/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x297/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x464/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x464/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x464/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4c8/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4c8/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4c8/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2ba/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2ba/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2ba/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x3cc/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3cc/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3cc/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2e7/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2e7/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2e7/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4b6/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4b6/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4b6/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x151/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x151/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x151/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b2/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4b2/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x4b2/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2eb/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2eb/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x2eb/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x142/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x142/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x142/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x266/flip_bit | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x266/zero | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C00-BASE/off=0x266/ff | CAP-C00-BASE | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x584/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x584/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x584/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x443/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x443/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x443/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30b/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x30b/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x30b/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x17f/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x17f/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x17f/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x393/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x393/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x393/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x31e/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x31e/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x31e/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2d3/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2d3/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2d3/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x173/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x173/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x173/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x357/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x357/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x357/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x329/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x329/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x329/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x4df/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x4df/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x4df/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x371/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x371/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x371/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x1b6/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x1b6/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x1b6/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2f1/flip_bit | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2f1/zero | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CAP-C62-DART/off=0x2f1/ff | CAP-C62-DART | FAIL | SILENT: corrupted input decoded identically |
| CLAUDE-GRADE-MARKER/off=0x72d/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x72d/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x72d/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x79f/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x79f/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x79f/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x77d/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x77d/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x77d/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x715/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x715/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x715/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x78d/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x78d/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x78d/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x725/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x725/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x725/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x71d/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x71d/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x71d/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x785/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x785/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x785/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x775/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x775/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x775/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x73f/flip_bit | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x73f/zero | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| CLAUDE-GRADE-MARKER/off=0x73f/ff | CLAUDE-GRADE-MARKER | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190e1/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190e1/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190e1/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18fa7/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18fa7/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18fa7/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19007/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19007/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19007/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19201/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19201/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19201/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x192c1/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x192c1/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x192c1/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19187/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19187/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19187/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1905f/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1905f/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1905f/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19237/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19237/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19237/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190b7/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190b7/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x190b7/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1906f/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1906f/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1906f/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1923f/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1923f/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x1923f/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19081/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19081/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19081/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19247/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19247/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19247/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18faf/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18faf/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x18faf/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19141/flip_bit | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19141/zero | 2303-BD137-PLACED | ok | ok (decode changed, as required) |
| 2303-BD137-PLACED/off=0x19141/ff | 2303-BD137-PLACED | ok | ok (decode changed, as required) |

## Unsupported (54)

- **CAP-C00-BASE/off=0x288/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x288/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x288/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x297/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x297/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x297/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4c8/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4c8/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4c8/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2ba/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2ba/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2ba/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2e7/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2e7/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2e7/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b6/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b6/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b6/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b2/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b2/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x4b2/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2eb/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2eb/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x2eb/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x266/flip_bit** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x266/zero** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C00-BASE/off=0x266/ff** (Oracle C, seed CAP-C00-BASE): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x30b/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x30b/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x30b/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x393/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x393/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x393/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x31e/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x31e/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x31e/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2d3/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2d3/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2d3/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x357/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x357/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x357/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x329/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x329/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x329/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x371/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x371/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x371/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x1b6/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x1b6/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x1b6/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2f1/flip_bit** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2f1/zero** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically
- **CAP-C62-DART/off=0x2f1/ff** (Oracle C, seed CAP-C62-DART): SILENT: corrupted input decoded identically

## Recommendations

- **Region-C snapshot / line-table shadow copies are parsed but not cross-validated.** 54 Oracle-C cases across CAP-C00-BASE, CAP-C62-DART corrupt a byte accumark_pds.decode_piece_block itself identifies as a coordinate (via dataset/templates.coord_offsets - never a guessed offset), yet neither `block['perimeter']` nor verify_capture's own `line_table_consistent` check changes. Each perimeter point is stored 5-7 times (the point table, two Region-C snapshots, and the line table); this finding is specifically about the snapshot/shadow copies, not the authoritative point-table copy (which Oracle C DOES catch - see the `ok` rows above). Representative offsets: 0x1b6, 0x266, 0x288, 0x297, 0x2ba, 0x2d3. Two honest paths forward: (a) extend accumark_pds.check_line_table (or a new check) to cross-validate Region-C's snapshots against the perimeter the same way the line table already is, so corruption there becomes detectable; or (b) if Region-C's snapshots are confirmed genuinely decorative/redundant (AccuMark writes them but never reads them back), document that explicitly in FORMAT_SPEC.md so a future reader does not spend time trying to cross-validate inert data. Not chased further in this session - it is a real, specific, reproducible finding, not a decoder defect introduced by v2, and resolving which of (a)/(b) is true needs a live AccuMark capture, not more offline analysis.
