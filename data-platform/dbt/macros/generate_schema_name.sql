{#
  カスタムスキーマ（+schema）を指定したモデルは、ターゲットのスキーマ名を前置せず、そのままのスキーマ名で作成する。
  例: analytics_staging ではなく staging
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
