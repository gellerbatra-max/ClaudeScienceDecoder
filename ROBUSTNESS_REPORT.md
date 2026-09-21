# Robustness report (v2)
decoder_version: accumark_pds=3.0 accumark_marker=3.0

561 cases, 561 passed, 0 failed, 123.0s

## Supported

- ZIP structural variants (Oracle A, 252/252): STORED/DEFLATED/BZIP2/LZMA and mixed compression, reversed/shuffled member order, folder prefixes, deep nesting, backslash paths, directory entries, extra junk members, non-ASCII/long names, `.TMP`/`.dat` renamed members, dropped `ver.5`/`comments.txt`, missing/replaced archive comment, zeroed timestamps - decode identically to the original on every seed.
- Malformed-input contract (Oracle B, 12/12): every case below raises a named `accumark_errors.AccuMarkError` subclass (or `zipfile.BadZipFile` for a non-ZIP container) - never `SystemExit`, never a bare `IndexError`/`struct.error`, never a silent wrong answer.

## Oracle A (252/252 ok)

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
| 2303-BD137-UNLAID/v_stored | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_deflated | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_bzip2 | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_lzma | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_mixed_compression | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_reversed_order | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_shuffled_order | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_folder_prefix | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_deep_nesting | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_backslash_paths | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_directory_entries | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_extra_junk | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_nonascii_name | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_long_name | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_upper_tmp | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_renamed_ext | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_drop_ver5 | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_drop_comments | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_no_comment | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_replaced_comment | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/v_zeroed_timestamps | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_stored | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_deflated | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_bzip2 | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_lzma | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_mixed_compression | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_reversed_order | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_shuffled_order | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_folder_prefix | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_deep_nesting | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_backslash_paths | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_directory_entries | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_extra_junk | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_nonascii_name | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_long_name | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_upper_tmp | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_renamed_ext | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_drop_ver5 | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_drop_comments | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_no_comment | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_replaced_comment | 2303-BD137-UNLAID | ok | ok |
| 2303-BD137-UNLAID/place_marker/v_zeroed_timestamps | 2303-BD137-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_stored | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_deflated | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_bzip2 | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_lzma | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_mixed_compression | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_reversed_order | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_shuffled_order | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_folder_prefix | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_deep_nesting | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_backslash_paths | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_directory_entries | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_extra_junk | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_nonascii_name | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_long_name | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_upper_tmp | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_renamed_ext | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_drop_ver5 | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_drop_comments | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_no_comment | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_replaced_comment | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/v_zeroed_timestamps | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_stored | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_deflated | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_bzip2 | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_lzma | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_mixed_compression | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_reversed_order | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_shuffled_order | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_folder_prefix | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_deep_nesting | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_backslash_paths | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_directory_entries | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_extra_junk | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_nonascii_name | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_long_name | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_upper_tmp | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_renamed_ext | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_drop_ver5 | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_drop_comments | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_no_comment | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_replaced_comment | 5683D-SS21-UNLAID | ok | ok |
| 5683D-SS21-UNLAID/place_marker/v_zeroed_timestamps | 5683D-SS21-UNLAID | ok | ok |
| CLAUDE-D2-M0/v_stored | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_deflated | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_bzip2 | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_lzma | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_mixed_compression | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_reversed_order | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_shuffled_order | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_folder_prefix | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_deep_nesting | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_backslash_paths | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_directory_entries | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_extra_junk | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_nonascii_name | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_long_name | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_upper_tmp | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_renamed_ext | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_drop_ver5 | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_drop_comments | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_no_comment | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_replaced_comment | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/v_zeroed_timestamps | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_stored | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_deflated | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_bzip2 | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_lzma | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_mixed_compression | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_reversed_order | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_shuffled_order | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_folder_prefix | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_deep_nesting | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_backslash_paths | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_directory_entries | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_extra_junk | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_nonascii_name | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_long_name | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_upper_tmp | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_renamed_ext | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_drop_ver5 | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_drop_comments | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_no_comment | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_replaced_comment | CLAUDE-D2-M0 | ok | ok |
| CLAUDE-D2-M0/place_marker/v_zeroed_timestamps | CLAUDE-D2-M0 | ok | ok |

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
| nested_wrapper_zip | synthetic-Drive-wrapper | ok | ok (NestedArchive) |
| truncated_object_123B_decode_zip | CAP-C00-BASE | ok | ok (NoSuchObject) |
| truncated_object_123B_list_zip | CAP-C00-BASE | ok | ok (no exception, as required) |
| truncated_object_200B_list_zip | 2303-BD137-PLACED | ok | ok (no exception, as required) |

## Oracle C (297/297 ok)

| case | seed | verdict | detail |
|---|---|---|---|
| CAP-C00-BASE/off=0x3de/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3de/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3de/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x288/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x288/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x288/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x297/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x297/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x297/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x464/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x464/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x464/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x37a/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4c8/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4c8/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4c8/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2bc/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2bc/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2bc/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3cc/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3cc/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x3cc/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2e9/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2e9/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2e9/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b6/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b6/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b6/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x151/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x151/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x151/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b2/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b2/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x4b2/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2ed/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2ed/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x2ed/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x142/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x142/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x142/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x266/flip_bit | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x266/zero | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C00-BASE/off=0x266/ff | CAP-C00-BASE | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x5d2/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x5d2/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x5d2/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x491/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x491/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x491/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x160/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30b/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30b/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30b/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x17f/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x17f/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x17f/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x431/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x431/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x431/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x31f/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x31f/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x31f/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2d3/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2d3/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2d3/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x173/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x173/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x173/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x366/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x366/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x366/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x344/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x344/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x344/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30f/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30f/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x30f/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x353/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x353/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x353/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2cf/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2cf/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x2cf/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x16f/flip_bit | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x16f/zero | CAP-C62-DART | ok | ok (decode changed, as required) |
| CAP-C62-DART/off=0x16f/ff | CAP-C62-DART | ok | ok (decode changed, as required) |
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
| 2303-BD137-UNLAID/off=0x46d6/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x46d6/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x46d6/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190a7/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190a7/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190a7/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x348a/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x348a/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x348a/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x46ce/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x46ce/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x46ce/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x192a0/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x192a0/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x192a0/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x191c7/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x191c7/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x191c7/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19045/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19045/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19045/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x3da8/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x3da8/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x3da8/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x1854/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x1854/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x1854/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19043/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19043/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19043/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19068/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19068/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19068/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19103/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19103/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19103/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c8/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c8/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c8/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19165/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19165/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x19165/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c9/flip_bit | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c9/zero | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 2303-BD137-UNLAID/off=0x190c9/ff | 2303-BD137-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5229/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5229/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5169/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5169/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5085/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5085/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5085/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5203/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5203/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5203/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x51c9/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x51c9/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e7/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e7/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e7/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x4f65/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x4f65/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x4f65/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0xa8c/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0xa8c/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0xa8c/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5205/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5205/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5205/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x163c/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x163c/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x163c/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e3/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e3/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x50e3/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x51e9/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x51e9/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x51e9/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x1388/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x1388/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x1388/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5220/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5220/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x5220/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x52a9/flip_bit | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x52a9/zero | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| 5683D-SS21-UNLAID/off=0x52a9/ff | 5683D-SS21-UNLAID | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2328/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2328/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2328/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x24c1/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x24c1/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x24c1/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0xb62/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0xb62/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0xb62/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2409/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2409/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2409/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2384/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2384/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2384/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x23e6/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x23e6/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x23e6/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c6/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c6/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c6/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2504/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2504/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2504/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2266/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2266/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2266/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x5fd/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x5fd/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x5fd/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x235b/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x235b/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x235b/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x1622/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x1622/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x1622/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x223b/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x223b/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x223b/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2324/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2324/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x2324/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c4/flip_bit | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c4/zero | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |
| CLAUDE-D2-M0/off=0x22c4/ff | CLAUDE-D2-M0 | ok | ok (decode changed, as required) |

## Unsupported (0)

None.

## Recommendations

History of two now-resolved Oracle-C findings, kept for context:
- **RESOLVED: Region-C snapshot cross-validation.** The earlier version of this report flagged snapshot1/snapshot2 (Region C's two perimeter re-listings) as parsed-but-not-cross-validated. Root cause turned out to be a real parser bug, not an unvalidated-but-correct redundant copy: `accumark_pds.parse_region_c` read snapshot2 (and, on notched/darted/annotated/curved pieces, part of snapshot1 too) from the wrong byte offset, so what was being reported as "snapshot data" was partly garbage from adjacent structures. Found by byte-searching for known-real coordinates around the reported offsets (not by guessing), fixed in `parse_region_c`/`parse_point_snapshot` (variable-width point records instead of a fixed 15-byte stride; a corrected offset for snapshot2's true start; the snapshot count is now `n_perimeter_a`, the same corners-minus-notches count `parse_pretable_header` already used for that other field). A new `accumark_pds.check_region_c` / `region_c_consistent` fact cross-validates both snapshots against the perimeter, wired into Oracle C's canon. Verified clean (`region_c_consistent=yes`, geometry matches) on every corpus fixture except the same three seam-allowanced pieces `check_line_table` already documents as a known, separate gap (CAP-C30-SEAM-UNEVEN, CAP-C31-SEAM-TAPER, TASK2-SEAM1CM - their uneven/tapered seam corners aren't plain per-corner offsets on either check).

- **RESOLVED: kind=2 "internal-line echo" points were over-covered by the seam-offset tolerance.** A follow-up session investigated the 9 Oracle-C cases the Region-C fix above left behind (CAP-C00-BASE, a piece with no seam allowance at all). Root cause: `kind=2` line-table records are not specific to seam allowance - they are the echo record for EVERY internal line (grain, drill, cutout), one per segment, present on any piece that has one, seamed or not (confirmed point-for-point exact on CAP-C00-BASE/CAP-C10-PENT/CAP-C50-DRILL1/CAP-C60-CUTOUT/CAP-C12-TWOINTLINES). `check_line_table`'s seam-offset leniency (`_is_seam_offset`, +-`SEAM_OFFSET_MAX`=2in) was being applied to every kind=2 record indiscriminately, so a corrupted echo point on a non-seam piece still landed "near" its own real, uncorrupted point by coincidence (sharing an axis with it) and was waved through as a plausible seam miter on a piece that was never seamed. Internal-line echoes are structurally distinct from genuine seam/cutline records by their points' own id field (`a == 65535`, unnumbered, vs a real numbered corner id on every seam/cutline point in the corpus - no fixture mixes the two within one record). Fixed: the leniency now only applies to points that carry a numbered id; an internal-line echo point must coincide exactly, like everything else. `robustness/run.py`'s Oracle C: 294/303 -> **303/303, all passing.**

No further Oracle-C gaps as of this run.
