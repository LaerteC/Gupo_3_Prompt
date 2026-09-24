{#
  Por padrão o dbt juntaria nomes (ex.: "main_silver").
  Esta macro faz a pasta "silver" virar o schema "silver", simples assim.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%} {{ target.schema }}
    {%- else -%} {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
