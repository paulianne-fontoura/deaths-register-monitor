{% macro normalize_name(column) %}
    trim(
        regexp_replace(
            regexp_replace(
                strip_accents(upper({{ column }})),
                '[^A-Z]', ' ', 'g'
            ),
            ' +', ' ', 'g'
        )
    )
{% endmacro %}
