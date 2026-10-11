# ダッシュボードとチャートのリネージの手動編集

Lightdash から取り込んだダッシュボードとチャートに、参照しているテーブルからのリネージを手動で追加する手順です。

## 背景

OpenMetadata 2.0.3 の Lightdash コネクタは、ダッシュボードとチャートを取り込みますが、それらがどのテーブルを参照しているかのリネージは作成しません（コネクタのリネージ作成処理が実装されていません）。そのため、取り込み直後のダッシュボードとチャートにはリネージがなく、テーブル側から「どのダッシュボードで使われているか」を辿れません。

一方、テーブル間のリネージ（raw → staging → intermediate → marts）は dbt の取り込みで作成されます。チャートとダッシュボードへのリネージを手動で追加すると、エクスポートファイルを取り込んだ raw テーブルからダッシュボードまでを一続きで辿れるようになります。

```
raw_* → staging → intermediate → marts のテーブル → チャート → ダッシュボード
└──────────── dbt の取り込みで作成 ────────────┘ └──── 手動で追加 ────┘
```

## 追加するリネージ

Lightdash のサンプルのチャート（`lightdash/setup/setup.py` で作成）は、次の marts のテーブルを参照しています。Lightdash の Explore のもとになるテーブルに加え、結合（joins）したテーブルのディメンションを使っている場合はそのテーブルも参照しています。

| 上流（テーブル） | 下流（チャート） | 備考 |
| --- | --- | --- |
| `marts.fct_orders` | 月別売上 | |
| `marts.fct_orders` | 会員ランク別の売上 | |
| `marts.dim_customers` | 会員ランク別の売上 | 会員ランク（`membership_rank`）を結合して使用 |
| `marts.fct_sessions` | キャンペーン別のコンバージョン率 | |
| `marts.dim_campaigns` | キャンペーン別のコンバージョン率 | キャンペーン名（`campaign_name`）を結合して使用 |
| `marts.fct_inquiries` | 問い合わせの種類別件数 | |

さらに、各チャートからダッシュボードへのリネージを追加します。

| 上流（チャート） | 下流（ダッシュボード） |
| --- | --- |
| 月別売上 | EC サイト KPI |
| 会員ランク別の売上 | EC サイト KPI |
| キャンペーン別のコンバージョン率 | EC サイト KPI |
| 問い合わせの種類別件数 | EC サイト KPI |

Lightdash のチャートとダッシュボードは、OpenMetadata では UUID が名前（FQN の末尾）になり、Lightdash 上の名前は表示名（Display Name）になります。検索や画面上では表示名で探します。

## UI で編集する

1. 上流のテーブル（例: `marts.fct_orders`）を開き、Lineage タブを表示します。dbt の取り込みで作成されたテーブル間のリネージが表示されます。
2. リネージの編集モードに切り替えます。
3. 下流に追加するチャート（例: 月別売上）を検索してリネージ図に追加します。
4. テーブルのノードの右端（下流側）から、チャートのノードの左端（上流側）に向かってドラッグし、エッジでつなぎます。
5. 同様に、チャートからダッシュボードへのエッジを追加します。
6. 編集モードを終了します。

上記の表のすべてのリネージを追加したら、ダッシュボード（EC サイト KPI）の Lineage タブを開き、上流をたどって raw テーブルまでつながっていることを確認します。

追加したエッジを選択すると、エッジの削除や説明の編集ができます。

## API で追加する

追加するリネージが多い場合や、環境を作り直すたびに同じリネージを追加する場合は、API を使います。リネージの追加は `PUT /api/v1/lineage` で、上流（`fromEntity`）と下流（`toEntity`）のエンティティの ID と種類を指定します。`lineageDetails.source` に `Manual` を指定すると、手動で追加したリネージとして記録されます。

```json
{
  "edge": {
    "fromEntity": {"id": "<テーブルの ID>", "type": "table"},
    "toEntity": {"id": "<チャートの ID>", "type": "chart"},
    "lineageDetails": {"source": "Manual"}
  }
}
```

エンティティの ID は、FQN を指定して取得します。

| エンティティ | 取得する API | FQN の例 |
| --- | --- | --- |
| テーブル | `GET /api/v1/tables/name/{fqn}` | `<データベースサービス名>.dwh.marts.fct_orders` |
| チャート | `GET /api/v1/charts/name/{fqn}` | `<ダッシュボードサービス名>.<Lightdash のチャートの UUID>` |
| ダッシュボード | `GET /api/v1/dashboards/name/{fqn}` | `<ダッシュボードサービス名>.<Lightdash のダッシュボードの UUID>` |

API の呼び出しには、OpenMetadata のアクセストークンが必要です。ボットのトークン（Settings > Bots）または個人アクセストークン（ユーザーのプロフィール画面）を使い、`Authorization: Bearer <トークン>` ヘッダーに指定します。

curl の例です。

```bash
OM=http://localhost:8585/api/v1
TOKEN=<アクセストークン>

TABLE_ID=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
  "${OM}/tables/name/<データベースサービス名>.dwh.marts.fct_orders" | jq -r .id)
CHART_ID=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
  "${OM}/charts/name/<ダッシュボードサービス名>.<チャートの UUID>" | jq -r .id)

curl -s -X PUT "${OM}/lineage" \
  -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
  -d "{\"edge\": {
        \"fromEntity\": {\"id\": \"${TABLE_ID}\", \"type\": \"table\"},
        \"toEntity\": {\"id\": \"${CHART_ID}\", \"type\": \"chart\"},
        \"lineageDetails\": {\"source\": \"Manual\"}
      }}"
```

リネージを削除する場合は、`DELETE /api/v1/lineage/{上流の種類}/{上流の ID}/{下流の種類}/{下流の ID}` を使います。

## 注意事項

- 手動で追加したリネージは Lightdash の定義と連動しません。Lightdash 側でチャートが参照するテーブルを変更した場合は、リネージも手動で更新します。
- Lightdash でチャートやダッシュボードを作り直すと UUID が変わり、OpenMetadata では別のエンティティとして取り込まれます。この場合はリネージを追加し直します。
