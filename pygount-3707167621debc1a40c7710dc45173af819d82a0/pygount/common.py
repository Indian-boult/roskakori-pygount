"""
Common classes and functions for pygount.
"""
# Copyright (c) 2016, Thomas Aglassinger.
# All rights reserved. Distributed under the BSD License.
import fnmatch
import re


__version__ = '0.4'


#: Pseudo pattern to indicate that the remaining pattern are an addition to the default patterns.
ADDITIONAL_PATTERN = '[...]'

#: Prefix to use for pattern strings to describe a regular expression instead of a shell pattern.
REGEX_PATTERN_PREFIX = '[regex]'

_REGEX_TYPE = type(re.compile(''))


class Error(Exception):
    pass


class OptionError(Error):
    def __init__(self, message, source=None):
        super().__init__(message)
        self.option_error_message = (source + ': ') if source is not None else ''
        self.option_error_message += message

    def __str__(self):
        return self.option_error_message


def as_list(items_or_text):
    """
    Convert items_or_text to a list.
    
    If items_or_text is a string, split it by commas and return as list.
    If it's already an iterable (except string), convert to list.
    Empty strings and None values are filtered out.
    
    Args:
        items_or_text: String with comma-separated values or any iterable
        
    Returns:
        List of items with whitespace stripped and empty items removed
    """
    if items_or_text is None:
        return []
    
    if isinstance(items_or_text, str):
        if not items_or_text.strip():
            return []
        # Split by comma, strip whitespace, and filter out empty strings
        return [item.strip() for item in items_or_text.split(',') if item.strip()]
    
    # For non-string iterables, convert to list
    try:
        return list(items_or_text)
    except TypeError:
        # If it's not iterable, return it as a single-item list
        return [items_or_text]


def regex_from(pattern, is_shell_pattern=False):
    """
    Convert a pattern to a compiled regular expression.
    
    Args:
        pattern: Can be a string pattern, compiled regex, or regex pattern object
        is_shell_pattern: If True, treat string patterns as shell patterns (with *, ?, etc.)
                         If False, treat as regular expressions
    
    Returns:
        Compiled regular expression object
        
    Raises:
        re.error: If the pattern cannot be compiled as a regular expression
    """
    if pattern is None or pattern == "":
        # Return a regex that matches nothing
        return re.compile(r'(?!.*)')
    
    # If it's already a compiled regex, return it as-is
    if isinstance(pattern, _REGEX_TYPE):
        return pattern
    
    # Convert string pattern to regex
    if isinstance(pattern, str):
        if is_shell_pattern:
            # Convert shell pattern to regex using fnmatch.translate
            regex_pattern = fnmatch.translate(pattern)
            return re.compile(regex_pattern)
        else:
            # Treat as regular expression pattern
            return re.compile(pattern)
    
    # For any other type, try to convert to string first
    return re.compile(str(pattern))


def regexes_from(patterns_text, default_patterns_text=None, source=None):
    assert patterns_text is not None

    result = []
    default_regexes = []
    try:
        if isinstance(patterns_text, str):
            is_shell_pattern = True
            patterns_text_without_prefixes = patterns_text
            if patterns_text_without_prefixes.startswith(REGEX_PATTERN_PREFIX):
                is_shell_pattern = False
                patterns_text_without_prefixes = patterns_text_without_prefixes[len(REGEX_PATTERN_PREFIX):]
            if patterns_text_without_prefixes.startswith(ADDITIONAL_PATTERN):
                assert default_patterns_text is not None
                default_regexes = regexes_from(default_patterns_text)
                patterns_text_without_prefixes = patterns_text_without_prefixes[len(ADDITIONAL_PATTERN):]

            patterns = as_list(patterns_text_without_prefixes)
            for pattern in patterns:
                result.append(regex_from(pattern, is_shell_pattern))
        else:
            regexes = list(patterns_text)
            if len(regexes) >= 1 and regexes[0] is None:
                default_regexes = regexes_from(default_patterns_text)
                regexes = regexes[1:]
            for supposed_regex in regexes:
                assert isinstance(supposed_regex, _REGEX_TYPE), \
                    'patterns_text must a text or sequnce or regular expressions but contains: %a' % supposed_regex
            result.extend(regexes)
    except re.error as error:
        raise OptionError(
            'cannot parse pattern for regular repression: {0}'.format(error),
            source)
    result.extend(default_regexes)
    return result


def matches_any(regexes, text):
    return any(regex.match(text) for regex in regexes)
