# 要件定義書

## はじめに

notion-relation-viewは、Notionのリレーション機能を視覚化するツールです。Obsidianのグラフビュー機能と同様に、各ノード（Notionページ）をリレーションで接続された線で表示するGUIを提供します。これにより、ユーザーはNotionページ間の関係構造を探索し、理解することができます。

このツールはWebアプリケーションとして実装され、NotionのEmbed（埋め込み）機能を使用してNotionページ内で利用できます。ユーザーはNotionページにこのツールのURLを埋め込むことで、Notion内でグラフビューを表示できます。この方式により、Webブラウザ版、デスクトップアプリ、モバイルアプリのすべてのプラットフォームで動作します。

## 用語集

- **System**: notion-relation-viewアプリケーション全体
- **Graph_Visualizer**: グラフの描画とレンダリングを担当するコンポーネント
- **Notion_API_Client**: Notion APIとの通信を処理するコンポーネント
- **Node**: グラフ上のNotionページを表す視覚要素
- **Edge**: ノード間のリレーションを表す接続線
- **Relation**: Notionデータベース内のページ間の関連付け
- **User**: アプリケーションを使用する人
- **Canvas**: グラフが描画される表示領域

## 要件

### 要件1: Notion APIとの接続

**ユーザーストーリー:** ユーザーとして、自分のNotionワークスペースに接続したい。そうすることで、ページとリレーションのデータを取得できる。

#### 受け入れ基準

1. WHEN ユーザーがNotion APIトークンを提供する THEN THE Notion_API_Client SHALL トークンを検証し、接続を確立する
2. WHEN 接続が成功する THEN THE System SHALL ユーザーにアクセス可能なデータベースとページのリストを表示する
3. IF 無効なAPIトークンが提供される THEN THE System SHALL 明確なエラーメッセージを表示し、再入力を促す
4. WHEN APIリクエストが失敗する THEN THE Notion_API_Client SHALL エラーをログに記録し、ユーザーに通知する

### 要件2: ページとリレーションデータの取得

**ユーザーストーリー:** ユーザーとして、Notionワークスペースからページとリレーション情報を取得したい。そうすることで、グラフを構築できる。

#### 受け入れ基準

1. WHEN ユーザーがデータ取得を開始する THEN THE Notion_API_Client SHALL すべてのアクセス可能なページのメタデータを取得する
2. WHEN ページデータを取得する THEN THE Notion_API_Client SHALL 各ページのリレーションプロパティを識別する
3. WHEN リレーションプロパティが見つかる THEN THE Notion_API_Client SHALL リレーション先のページIDを抽出する
4. WHEN データ取得が完了する THEN THE System SHALL 取得したページ数とリレーション数を表示する
5. WHERE ページにリレーションプロパティが存在しない THEN THE System SHALL そのページを孤立ノードとして扱う

### 要件3: グラフの視覚化

**ユーザーストーリー:** ユーザーとして、ページとリレーションをグラフとして視覚化したい。そうすることで、関係構造を理解できる。

#### 受け入れ基準

1. WHEN データが取得される THEN THE Graph_Visualizer SHALL 各ページをノードとして描画する
2. WHEN ノードを描画する THEN THE Graph_Visualizer SHALL ページタイトルをノードラベルとして表示する
3. WHEN リレーションが存在する THEN THE Graph_Visualizer SHALL ノード間にエッジを描画する
4. WHEN グラフを初期化する THEN THE Graph_Visualizer SHALL ノードを見やすく配置するレイアウトアルゴリズムを適用する
5. THE Graph_Visualizer SHALL ノードとエッジを区別できる視覚スタイルを使用する

### 要件4: インタラクティブな操作

**ユーザーストーリー:** ユーザーとして、グラフを操作したい。そうすることで、詳細を探索し、ビューをカスタマイズできる。

#### 受け入れ基準

1. WHEN ユーザーがノードをクリックする THEN THE System SHALL Notionでそのページを開く
2. WHEN ユーザーがノードをドラッグする THEN THE Graph_Visualizer SHALL ノードの位置を更新し、接続されたエッジを再描画する
3. WHEN ユーザーがキャンバスをドラッグする THEN THE Graph_Visualizer SHALL ビュー全体をパンする
4. WHEN ユーザーがスクロールする THEN THE Graph_Visualizer SHALL ズームレベルを調整する

### 要件5: フィルタリングと検索

**ユーザーストーリー:** ユーザーとして、特定のページやリレーションを見つけたい。そうすることで、大規模なグラフでも効率的にナビゲートできる。

#### 受け入れ基準

1. WHEN アプリケーションが起動する THEN THE System SHALL デフォルトで空のグラフを表示する
2. WHEN ユーザーがデータベースを選択して表示する THEN THE System SHALL そのデータベースに属するノードとそれらに接続されたエッジを表示する
3. WHEN 複数のデータベースが選択される THEN THE System SHALL すべての選択されたデータベースのノードとエッジを表示する
4. WHEN ユーザーが検索クエリを入力する THEN THE System SHALL クエリに一致するページタイトルを持つノードをハイライトする
5. WHEN 検索結果が見つかる THEN THE Graph_Visualizer SHALL 最初の一致するノードにビューを中央揃えする

### 要件6: ビュー管理とデータ永続化

**ユーザーストーリー:** ユーザーとして、複数のビュー設定を保存・管理したい。そうすることで、異なる目的に応じてグラフの表示を切り替えられる。

#### 受け入れ基準

1. WHEN ユーザーがAPIトークンを入力する THEN THE System SHALL トークンを安全にサーバーに保存する
2. WHEN アプリケーションが起動する THEN THE System SHALL 保存されたAPIトークンを読み込み、自動的に接続を試みる
3. WHEN ユーザーがビュー設定を作成する THEN THE System SHALL ビュー名、選択されたデータベース、ズームレベル、パン位置を保存し、一意のビューIDを生成する
4. WHEN ビュー設定が作成される THEN THE System SHALL そのビュー専用のURL（例: /view/{viewId}）を生成する
5. WHEN ユーザーがビュー専用URLにアクセスする THEN THE System SHALL そのビュー設定を読み込み、グラフを表示する
6. WHEN ユーザーが複数のビュー設定を作成する THEN THE System SHALL すべてのビュー設定とそれぞれのURLをリスト表示する
7. WHEN ユーザーがビュー設定を選択する THEN THE System SHALL そのビュー設定を読み込み、グラフを更新する
8. WHEN ユーザーがビュー設定を更新する THEN THE System SHALL 変更を保存し、次回選択時に反映する
9. WHEN ユーザーがビュー設定を削除する THEN THE System SHALL そのビュー設定とURLをリストから削除する
10. WHEN ユーザーがビューURLをNotionに埋め込む THEN THE System SHALL そのビューの設定でグラフを表示する
11. WHEN アプリケーションが再起動される THEN THE System SHALL 前回選択していたビュー設定を復元する

### 要件7: エラーハンドリングとユーザーフィードバック

**ユーザーストーリー:** ユーザーとして、操作の進行状況とエラーを理解したい。そうすることで、問題が発生したときに適切に対応できる。

#### 受け入れ基準

1. WHEN データ取得が進行中である THEN THE System SHALL 進行状況インジケーターを表示する
2. WHEN 長時間実行される操作が実行される THEN THE System SHALL 推定残り時間または進行状況パーセンテージを表示する
3. IF ネットワークエラーが発生する THEN THE System SHALL ユーザーフレンドリーなエラーメッセージを表示し、再試行オプションを提供する
4. IF APIレート制限に達する THEN THE System SHALL ユーザーに通知し、再試行までの待機時間を表示する
5. WHEN エラーが発生する THEN THE System SHALL エラーの詳細をコンソールログに記録する

### 要件8: パフォーマンスとスケーラビリティ

**ユーザーストーリー:** ユーザーとして、大規模なワークスペースでもスムーズに動作するツールが欲しい。そうすることで、多数のページがあっても使用できる。

#### 受け入れ基準

1. WHEN グラフに100以上のノードが含まれる THEN THE Graph_Visualizer SHALL 60FPSでレンダリングを維持する
2. WHEN ユーザーがズームまたはパンする THEN THE System SHALL 200ミリ秒以内に応答する
3. WHEN 大量のデータを処理する THEN THE System SHALL 仮想化またはレベル・オブ・ディテール技術を使用してパフォーマンスを最適化する
4. WHEN データ取得が実行される THEN THE Notion_API_Client SHALL リクエストをバッチ処理してAPI呼び出しを最小化する
