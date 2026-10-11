{#
  列の値が 0 以上であることを確認する。
#}
{% test non_negative(model, column_name) %}
    select *
    from {{ model }}
    where {{ column_name }} < 0
{% endtest %}
