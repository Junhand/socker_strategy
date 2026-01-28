# サッカー練習メニュー生成システム

画像とサッカーに関連する情報を元に、練習メニューを画像で解説するExcelを作成するリポジトリです。

## システム概要

```
ユーザー入力 → LLM処理 → 画像合成 → Excel生成 → ダウンロード
```

## LLMの処理過程

### 1. 入力処理

ユーザーが練習課題（例：「4人でのパス練習」）を入力すると、システムは以下の流れで処理を開始します。

```
[Web UI / CLI] → [FastAPI] → [PracticeMenuAgent] → [LLMClient]
```

### 2. LLMへのプロンプト送信

`src/llm_client.py` で GPT-4o にリクエストを送信します。

#### システムプロンプト（抜粋）

```
あなたはサッカーの練習メニューを設計する専門家です。
ユーザーから練習の課題を受け取り、具体的な練習ステップを設計してください。
```

LLMには以下の情報を構造化JSONで返すよう指示しています：

- **title**: 練習メニューのタイトル
- **description**: 練習の概要説明
- **steps**: 各練習ステップの配列
  - **step_number**: ステップ番号
  - **name**: ステップ名
  - **description**: 説明
  - **duration_minutes**: 所要時間
  - **players**: 選手の配置情報
  - **movements**: 選手の動き
  - **ball_movements**: ボールの動き
- **key_points**: 重要ポイント

#### 座標系

位置情報は正規化座標（0.0〜1.0）で表現されます：
- `x=0`: フィールド左端
- `x=1`: フィールド右端
- `y=0`: フィールド上端
- `y=1`: フィールド下端

### 3. LLMレスポンス例

```json
{
  "title": "4人パス練習メニュー",
  "description": "4人でボールを回しながらパスの精度と連携を高める練習",
  "steps": [
    {
      "step_number": 1,
      "name": "四角形パス回し",
      "description": "4人が四角形に配置し、時計回りにパスを回す",
      "duration_minutes": 5,
      "players": [
        {"id": "A", "position": {"x": 0.3, "y": 0.3}, "role": "パサー"},
        {"id": "B", "position": {"x": 0.7, "y": 0.3}, "role": "レシーバー"},
        {"id": "C", "position": {"x": 0.7, "y": 0.7}, "role": "パサー"},
        {"id": "D", "position": {"x": 0.3, "y": 0.7}, "role": "レシーバー"}
      ],
      "ball_movements": [
        {"from": {"x": 0.3, "y": 0.3}, "to": {"x": 0.7, "y": 0.3}, "type": "pass"}
      ]
    }
  ],
  "key_points": ["インサイドキックを正確に", "声を出してコミュニケーション"]
}
```

### 4. 画像合成処理

`src/image_composer.py` でLLMの出力を元に図解画像を生成します。

```
[ground.png] + [person.png] + [矢印・ライン描画] → [合成画像]
```

#### 描画要素

| 要素 | 色 | スタイル | 説明 |
|------|-----|---------|------|
| 選手 | - | person.png | フィールド上に配置 |
| 選手ラベル | 黒 | 白背景テキスト | A, B, C などのID |
| ボールの動き | オレンジ | 破線 + 矢印 | パス・シュートなど |
| 選手の動き | 青 | 実線 + 矢印 | ランニング・移動 |

### 5. Excel生成

`src/excel_generator.py` で最終的なExcelファイルを作成します。

#### シート構成

```
┌─────────────────────────────────────────────┐
│            練習メニュータイトル               │
├─────────────────────────────────────────────┤
│            練習の概要説明                     │
├────┬──────────────┬─────────────┬──────────┤
│ #  │     図解     │    説明     │   時間   │
├────┼──────────────┼─────────────┼──────────┤
│ 1  │   [画像]     │ ステップ説明 │   5分   │
├────┼──────────────┼─────────────┼──────────┤
│ 2  │   [画像]     │ ステップ説明 │   5分   │
├────┴──────────────┴─────────────┴──────────┤
│ 📌 重要ポイント                              │
│ • ポイント1                                  │
│ • ポイント2                                  │
└─────────────────────────────────────────────┘
```

## 処理フロー図

```
┌────────────────┐
│  ユーザー入力   │  「4人でのパス練習」
└───────┬────────┘
        ▼
┌────────────────┐
│  LLMClient     │  OpenRouter or Azure OpenAI (GPT-4o)
│  プロンプト送信 │
└───────┬────────┘
        ▼
┌────────────────┐
│  JSON解析      │  練習プラン構造化データ
└───────┬────────┘
        ▼
┌────────────────┐
│ ImageComposer  │  各ステップの図解生成
│ 画像合成       │  ground.png + person.png + 矢印
└───────┬────────┘
        ▼
┌────────────────┐
│ ExcelGenerator │  Excelファイル作成
│ シート作成      │  画像埋め込み + 説明文
└───────┬────────┘
        ▼
┌────────────────┐
│  ファイル出力   │  practice_menu.xlsx
└────────────────┘
```

## セットアップ

### 1. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .envファイルを作成
cp .env.sample .env
```

#### Option 1: OpenRouter を使用する場合

```bash
export OPENROUTER_API_KEY=your_api_key_here
# オプション: モデル指定 (デフォルト: openai/gpt-4o)
export OPENROUTER_MODEL=openai/gpt-4o
```

OpenRouter APIキーは https://openrouter.ai/keys で取得できます。

#### Option 2: Azure OpenAI を使用する場合

```bash
export AZURE_OPENAI_API_KEY=your_azure_api_key_here
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=gpt-4o
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

Azure OpenAIの環境変数が設定されている場合、自動的にAzure OpenAIが使用されます。

## 使用方法

### Web UI（推奨）

```bash
# サーバー起動
python api.py

# または
uvicorn api:app --reload --port 8000
```

ブラウザで http://localhost:8000 にアクセス

### CLI

```bash
# 基本的な使い方
python main.py "4人でのパス練習"

# 出力ファイル名を指定
python main.py "シュート練習" -o shooting.xlsx

# 標準入力から
echo "守備練習" | python main.py
```

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | Web UI |
| POST | `/api/generate` | 練習メニュー生成 |
| GET | `/api/health` | ヘルスチェック |

### POST /api/generate

**リクエスト:**
```json
{
  "challenge": "4人でのパス練習"
}
```

**レスポンス:** Excelファイル（application/vnd.openxmlformats-officedocument.spreadsheetml.sheet）

## ファイル構成

```
socker_strategy/
├── api.py                 # FastAPI バックエンド
├── main.py                # CLI エントリーポイント
├── requirements.txt       # 依存関係
├── .env.sample           # 環境変数サンプル
├── static/
│   └── index.html         # Web フロントエンド
├── src/
│   ├── __init__.py
│   ├── agent.py           # メインエージェント（オーケストレーション）
│   ├── llm_client.py      # LLMクライアント (OpenRouter / Azure OpenAI)
│   ├── image_composer.py  # 画像合成エンジン
│   └── excel_generator.py # Excel生成エンジン
└── images/
    ├── ground.png         # サッカーフィールド画像
    └── person.png         # 人物アイコン
```

## 技術スタック

- **Backend**: FastAPI, Python 3.10+
- **LLM**: OpenRouter API または Azure OpenAI (GPT-4o)
- **Excel**: openpyxl
- **画像処理**: Pillow
- **Frontend**: HTML/CSS/JavaScript (Vanilla)

## LLMプロバイダーの自動検出

システムは環境変数に基づいてLLMプロバイダーを自動検出します：

| 環境変数 | 使用されるプロバイダー |
|---------|---------------------|
| `AZURE_OPENAI_API_KEY` が設定されている | Azure OpenAI |
| `OPENROUTER_API_KEY` のみ設定 | OpenRouter |

プログラムから明示的に指定することも可能です：

```python
from src.llm_client import LLMClient

# OpenRouter を明示的に使用
client = LLMClient(provider="openrouter")

# Azure OpenAI を明示的に使用
client = LLMClient(provider="azure")
```

## 画像生成の制限事項

現在の画像合成エンジン（`image_composer.py`）には以下の制限があります：

### 描画できないもの

| 項目 | 説明 |
|------|------|
| ボールアイコン | ボールは矢印線のみで表現（アイコン表示なし） |
| コーン・マーカー | 練習用コーンやマーカーの表示は未対応 |
| ゴール | ゴールポストの描画は未対応（フィールド画像に含まれている場合のみ） |
| 曲線の動き | ドリブルやカーブランなどの曲線パスは直線で近似 |
| 複数チームの色分け | 全選手が同じアイコンで表示される |
| 選手の向き | 選手アイコンに向きの概念がない |

### 表現が難しいもの

| 項目 | 説明 |
|------|------|
| 複雑な連携プレー | 多数の矢印が重なると視認性が低下 |
| 時間経過の表現 | 1ステップ = 1画像のため、連続した動きは複数ステップに分割が必要 |
| 3D的な表現 | 高さやジャンプなどの立体的な動きは表現不可 |
| 細かいポジション調整 | LLMが生成する座標の精度に依存 |
| フィールドの一部拡大 | 常にフィールド全体が表示される |

### 回避策

- **複雑な動き**: 複数のステップに分割して段階的に説明
- **チーム分け**: ステップの説明文で「攻撃側: A, B」「守備側: C, D」と記載
- **細かい位置**: Excel出力後に画像を手動で調整可能

### 将来的な改善候補

- [ ] ボール・コーン等のアイコン追加
- [ ] チームカラー対応（赤/青など）
- [ ] 曲線パスの描画
- [ ] フィールド部分拡大表示
- [ ] アニメーションGIF出力
