# 要件定義書

## はじめに

subscription-managementは、notion-relation-viewアプリケーションにサブスクリプションベースの収益化機能を追加する機能です。この機能により、ユーザーは無料プランとProプランの2つのティアから選択でき、それぞれのプランに応じた機能制限とアクセス権が適用されます。

この機能は、ユーザーのサブスクリプション管理、プラン制限の適用、決済処理、使用状況の追跡、請求書管理を含みます。既存のnotion-relation-viewアプリケーションに統合され、シームレスなユーザー体験を提供します。

## 用語集

- **System**: subscription-management機能を含むnotion-relation-viewアプリケーション全体
- **Subscription_Manager**: ユーザーのサブスクリプション状態を管理するコンポーネント
- **Payment_Processor**: 決済処理とトランザクションを処理するコンポーネント
- **Usage_Tracker**: ユーザーの使用状況（ビュー数、ノード数など）を追跡するコンポーネント
- **Plan_Enforcer**: プラン制限を適用し、機能アクセスを制御するコンポーネント
- **User**: アプリケーションを使用する人
- **Free_Plan**: 無料プラン（1ビュー、100ノード制限）
- **Pro_Plan**: 有料プラン（月額$10、無制限ビュー・ノード）
- **View_Configuration**: ユーザーが作成したグラフビューの設定
- **Node**: グラフ上のNotionページを表す視覚要素
- **Grace_Period**: 制限超過時にユーザーがアップグレードまたは調整できる猶予期間

## 要件

### 要件1: サブスクリプションプランの定義

**ユーザーストーリー:** システム管理者として、2つの明確なサブスクリプションティアを定義したい。そうすることで、ユーザーに適切な機能とリソース制限を提供できる。

#### 受け入れ基準

1. THE System SHALL Free_Planを定義し、1つのView_Configuration、100ノードの制限、基本的なグラフ操作、基本的なフィルタリングを含む
2. THE System SHALL Pro_Planを定義し、無制限のView_Configuration、無制限のノード、エクスポート機能（PNG/SVG）、カスタムカラーテーマ、高度なフィルタリング、グラフレイアウトアルゴリズムの選択、優先サポートを含む
3. THE System SHALL Pro_Planの価格を月額$10として設定する
4. THE System SHALL すべての新規ユーザーにデフォルトでFree_Planを割り当てる
5. THE System SHALL 両プランでリアルタイムデータ更新を提供する

### 要件2: ユーザー登録とサブスクリプション初期化

**ユーザーストーリー:** 新規ユーザーとして、アカウントを作成し、サブスクリプションを開始したい。そうすることで、アプリケーションを使用できる。

#### 受け入れ基準

1. WHEN ユーザーがアカウントを作成する THEN THE Subscription_Manager SHALL そのユーザーにFree_Planを割り当てる
2. WHEN サブスクリプションが初期化される THEN THE System SHALL ユーザーの使用状況カウンター（ビュー数、ノード数）をゼロに設定する
3. WHEN ユーザーがログインする THEN THE System SHALL 現在のプラン情報と使用状況を表示する
4. WHEN サブスクリプションが作成される THEN THE Subscription_Manager SHALL サブスクリプション開始日を記録する

### 要件3: プランのアップグレード

**ユーザーストーリー:** Free_Planユーザーとして、Pro_Planにアップグレードしたい。そうすることで、より多くの機能とリソースにアクセスできる。

#### 受け入れ基準

1. WHEN Free_PlanユーザーがPro_Planへのアップグレードを開始する THEN THE System SHALL 決済情報入力フォームを表示する
2. WHEN ユーザーが有効な決済情報を提供する THEN THE Payment_Processor SHALL 決済情報を検証し、初回請求を処理する
3. WHEN 決済が成功する THEN THE Subscription_Manager SHALL ユーザーのプランをPro_Planに更新する
4. WHEN プランがアップグレードされる THEN THE System SHALL すべてのPro_Plan機能へのアクセスを即座に有効化する
5. WHEN アップグレードが完了する THEN THE System SHALL ユーザーに確認メールを送信する
6. IF 決済が失敗する THEN THE System SHALL エラーメッセージを表示し、ユーザーにFree_Planを維持する

### 要件4: プランのダウングレード

**ユーザーストーリー:** Pro_Planユーザーとして、Free_Planにダウングレードしたい。そうすることで、サブスクリプション費用を節約できる。

#### 受け入れ基準

1. WHEN Pro_PlanユーザーがFree_Planへのダウングレードを開始する THEN THE System SHALL ダウングレードの影響（制限、機能喪失）を説明する確認ダイアログを表示する
2. WHEN ユーザーがダウングレードを確認する THEN THE Subscription_Manager SHALL 現在の請求期間の終了時にダウングレードをスケジュールする
3. WHEN 請求期間が終了する THEN THE Subscription_Manager SHALL ユーザーのプランをFree_Planに更新する
4. WHEN ダウングレードが適用される THEN THE Plan_Enforcer SHALL Free_Planの制限を適用する
5. WHEN ダウングレードが完了する THEN THE System SHALL ユーザーに確認メールを送信する
6. WHEN ユーザーがFree_Planの制限を超えるリソースを持つ THEN THE System SHALL 超過分の処理方法（削除、無効化）をユーザーに通知する

### 要件5: サブスクリプションのキャンセル

**ユーザーストーリー:** Pro_Planユーザーとして、サブスクリプションをキャンセルしたい。そうすることで、今後の請求を停止できる。

#### 受け入れ基準

1. WHEN Pro_Planユーザーがサブスクリプションのキャンセルを開始する THEN THE System SHALL キャンセルの影響を説明する確認ダイアログを表示する
2. WHEN ユーザーがキャンセルを確認する THEN THE Subscription_Manager SHALL 現在の請求期間の終了時にキャンセルをスケジュールする
3. WHEN 請求期間が終了する THEN THE Subscription_Manager SHALL サブスクリプションをキャンセルし、ユーザーをFree_Planに移行する
4. WHEN キャンセルがスケジュールされる THEN THE Payment_Processor SHALL 今後の自動請求を停止する
5. WHEN キャンセルが完了する THEN THE System SHALL ユーザーに確認メールを送信する
6. WHEN ユーザーがキャンセル後にアクセスする THEN THE System SHALL 請求期間終了までPro_Plan機能へのアクセスを維持する

### 要件6: ビュー設定数の制限適用

**ユーザーストーリー:** システムとして、ユーザーのプランに基づいてビュー設定数を制限したい。そうすることで、プラン間の価値差を維持できる。

#### 受け入れ基準

1. WHEN Free_Planユーザーがビュー設定を作成しようとする THEN THE Plan_Enforcer SHALL 既存のビュー設定数を確認する
2. WHEN Free_Planユーザーが既に1つのビュー設定を持つ THEN THE System SHALL 新しいビュー設定の作成を拒否し、アップグレードプロンプトを表示する
3. WHEN Pro_Planユーザーがビュー設定を作成しようとする THEN THE System SHALL 制限なく作成を許可する
4. WHEN ユーザーがビュー設定リストを表示する THEN THE System SHALL 現在の使用状況（X/Y ビュー）とプラン制限を表示する
5. WHEN Free_Planユーザーが制限に達する THEN THE System SHALL Pro_Planへのアップグレードを促すメッセージを表示する

### 要件7: ノード数の制限適用

**ユーザーストーリー:** システムとして、ユーザーのプランに基づいてグラフ内のノード数を制限したい。そうすることで、リソース使用を管理し、プラン価値を維持できる。

#### 受け入れ基準

1. WHEN Free_Planユーザーがグラフをロードする THEN THE Usage_Tracker SHALL グラフ内のノード数をカウントする
2. WHEN ノード数が100を超える THEN THE Plan_Enforcer SHALL 最初の100ノードのみを表示し、残りを非表示にする
3. WHEN ノード制限が適用される THEN THE System SHALL ユーザーに制限メッセージとアップグレードオプションを表示する
4. WHEN Pro_Planユーザーがグラフをロードする THEN THE System SHALL すべてのノードを制限なく表示する
5. WHEN Free_Planユーザーがノード数を確認する THEN THE System SHALL 現在の表示ノード数と制限（100/100ノード）を表示する

### 要件8: 機能アクセス制御

**ユーザーストーリー:** システムとして、ユーザーのプランに基づいて機能へのアクセスを制御したい。そうすることで、Pro_Plan限定機能を保護できる。

#### 受け入れ基準

1. WHEN Free_Planユーザーがエクスポート機能にアクセスしようとする THEN THE Plan_Enforcer SHALL アクセスを拒否し、Pro_Plan限定機能であることを通知する
2. WHEN Free_Planユーザーがカスタムカラーテーマにアクセスしようとする THEN THE Plan_Enforcer SHALL アクセスを拒否し、アップグレードプロンプトを表示する
3. WHEN Free_Planユーザーが高度なフィルタリング（複数条件、正規表現）を使用しようとする THEN THE Plan_Enforcer SHALL アクセスを拒否し、基本フィルタリングのみを許可する
4. WHEN Free_Planユーザーがグラフレイアウトアルゴリズムを変更しようとする THEN THE Plan_Enforcer SHALL デフォルトアルゴリズムのみを許可する
5. WHEN Pro_Planユーザーが任意の機能にアクセスする THEN THE System SHALL すべての機能へのアクセスを許可する
6. WHEN ユーザーがPro_Plan限定機能を表示する THEN THE System SHALL Free_Planユーザーに「Pro」バッジを表示する

### 要件9: 決済処理

**ユーザーストーリー:** システムとして、安全かつ確実に決済を処理したい。そうすることで、収益を確保し、ユーザーの決済情報を保護できる。

#### 受け入れ基準

1. WHEN ユーザーが決済情報を入力する THEN THE Payment_Processor SHALL 決済情報を暗号化して保存する
2. WHEN Pro_Planサブスクリプションが開始される THEN THE Payment_Processor SHALL 初回請求（$10）を処理する
3. WHEN 月次請求日が到来する THEN THE Payment_Processor SHALL 自動的に月額料金（$10）を請求する
4. WHEN 決済が成功する THEN THE Payment_Processor SHALL トランザクション記録を作成し、領収書を生成する
5. IF 決済が失敗する THEN THE Payment_Processor SHALL ユーザーに通知し、決済情報の更新を促す
6. WHEN 決済が3回連続で失敗する THEN THE Subscription_Manager SHALL サブスクリプションを一時停止し、ユーザーに警告する
7. THE Payment_Processor SHALL PCI DSS準拠の決済ゲートウェイを使用する

### 要件10: 使用状況の追跡

**ユーザーストーリー:** システムとして、ユーザーの使用状況を追跡したい。そうすることで、プラン制限を適用し、使用パターンを分析できる。

#### 受け入れ基準

1. WHEN ユーザーがビュー設定を作成する THEN THE Usage_Tracker SHALL ビュー設定カウンターを増加させる
2. WHEN ユーザーがビュー設定を削除する THEN THE Usage_Tracker SHALL ビュー設定カウンターを減少させる
3. WHEN ユーザーがグラフをロードする THEN THE Usage_Tracker SHALL 表示されるノード数を記録する
4. WHEN ユーザーが機能を使用する THEN THE Usage_Tracker SHALL 機能使用イベント（エクスポート、フィルタリングなど）を記録する
5. WHEN 管理者が使用状況を確認する THEN THE System SHALL ユーザーごとの使用統計（ビュー数、ノード数、機能使用頻度）を表示する
6. THE Usage_Tracker SHALL 使用状況データをリアルタイムで更新する

### 要件11: 請求書と領収書の管理

**ユーザーストーリー:** Pro_Planユーザーとして、請求書と領収書を確認・ダウンロードしたい。そうすることで、支払い履歴を管理できる。

#### 受け入れ基準

1. WHEN 決済が完了する THEN THE System SHALL 請求書と領収書を自動生成する
2. WHEN ユーザーが請求履歴を表示する THEN THE System SHALL すべての過去の請求書をリスト表示する
3. WHEN ユーザーが請求書を選択する THEN THE System SHALL 請求書の詳細（日付、金額、プラン、決済方法）を表示する
4. WHEN ユーザーが領収書をダウンロードする THEN THE System SHALL PDF形式の領収書を生成する
5. WHEN 請求書が生成される THEN THE System SHALL ユーザーにメールで領収書を送信する
6. THE System SHALL 請求書に必要な情報（会社名、住所、税務情報）を含める

### 要件12: プラン比較とアップグレードプロンプト

**ユーザーストーリー:** Free_Planユーザーとして、プラン間の違いを理解し、アップグレードの価値を知りたい。そうすることで、適切なプランを選択できる。

#### 受け入れ基準

1. WHEN ユーザーがプラン比較ページを表示する THEN THE System SHALL Free_PlanとPro_Planの機能を並べて比較表示する
2. WHEN Free_Planユーザーが制限に達する THEN THE System SHALL Pro_Planの利点を強調するアップグレードプロンプトを表示する
3. WHEN ユーザーがPro_Plan限定機能にアクセスしようとする THEN THE System SHALL その機能の説明とアップグレードボタンを含むモーダルを表示する
4. WHEN アップグレードプロンプトが表示される THEN THE System SHALL 「今すぐアップグレード」と「後で」のオプションを提供する
5. WHEN ユーザーが「今すぐアップグレード」を選択する THEN THE System SHALL 決済フローに直接遷移する
6. THE System SHALL アップグレードプロンプトを過度に表示せず、ユーザー体験を損なわない

### 要件13: 猶予期間の処理

**ユーザーストーリー:** システムとして、ユーザーが制限を超えた場合に猶予期間を提供したい。そうすることで、ユーザーがアップグレードまたは調整する時間を与えられる。

#### 受け入れ基準

1. WHEN Pro_PlanユーザーがFree_Planにダウングレードし、2つ以上のビュー設定を持つ THEN THE System SHALL 7日間のGrace_Periodを提供する
2. WHEN Grace_Period中である THEN THE System SHALL ユーザーにすべてのビュー設定へのアクセスを許可する
3. WHEN Grace_Period中である THEN THE System SHALL ユーザーに残り日数と必要なアクション（ビュー削除またはアップグレード）を通知する
4. WHEN Grace_Periodが終了する THEN THE Plan_Enforcer SHALL 最も古いビュー設定を自動的に無効化し、1つのみをアクティブに保つ
5. WHEN ユーザーがGrace_Period中にビュー設定を削除する THEN THE System SHALL Grace_Periodを終了し、通常のFree_Plan制限を適用する
6. WHEN ユーザーがGrace_Period中にアップグレードする THEN THE System SHALL Grace_Periodをキャンセルし、Pro_Planを適用する

### 要件14: 決済失敗時の処理

**ユーザーストーリー:** システムとして、決済失敗時に適切に対応したい。そうすることで、ユーザーにサービスを継続提供しつつ、収益を保護できる。

#### 受け入れ基準

1. WHEN 月次請求が失敗する THEN THE Payment_Processor SHALL ユーザーにメールで通知する
2. WHEN 初回決済失敗が発生する THEN THE System SHALL 3日後に自動的に再試行する
3. WHEN 2回目の決済失敗が発生する THEN THE System SHALL さらに3日後に再試行し、緊急通知を送信する
4. WHEN 3回目の決済失敗が発生する THEN THE Subscription_Manager SHALL サブスクリプションを一時停止し、ユーザーをFree_Planに移行する
5. WHEN サブスクリプションが一時停止される THEN THE System SHALL ユーザーに決済情報の更新と再アクティブ化の方法を通知する
6. WHEN ユーザーが決済情報を更新し、決済が成功する THEN THE Subscription_Manager SHALL サブスクリプションを再アクティブ化し、Pro_Planを復元する

### 要件15: サブスクリプション状態の管理

**ユーザーストーリー:** システムとして、サブスクリプションの状態を正確に管理したい。そうすることで、ユーザーに適切なサービスレベルを提供できる。

#### 受け入れ基準

1. THE Subscription_Manager SHALL サブスクリプション状態（active、canceled、suspended、past_due）を維持する
2. WHEN サブスクリプションがactiveである THEN THE System SHALL ユーザーのプランに応じたすべての機能を提供する
3. WHEN サブスクリプションがcanceledである THEN THE System SHALL 請求期間終了までPro_Plan機能を提供し、その後Free_Planに移行する
4. WHEN サブスクリプションがsuspendedである THEN THE System SHALL ユーザーをFree_Planに移行し、再アクティブ化オプションを表示する
5. WHEN サブスクリプションがpast_dueである THEN THE System SHALL Pro_Plan機能へのアクセスを維持しつつ、決済更新を促す警告を表示する
6. WHEN サブスクリプション状態が変更される THEN THE Subscription_Manager SHALL 変更をログに記録し、ユーザーに通知する

### 要件16: 管理者機能

**ユーザーストーリー:** システム管理者として、サブスクリプションとユーザーを管理したい。そうすることで、カスタマーサポートと収益管理を効率化できる。

#### 受け入れ基準

1. WHEN 管理者がダッシュボードにアクセスする THEN THE System SHALL すべてのユーザーのサブスクリプション状態を表示する
2. WHEN 管理者がユーザーを検索する THEN THE System SHALL ユーザーのサブスクリプション詳細、使用状況、決済履歴を表示する
3. WHEN 管理者がユーザーのプランを変更する THEN THE Subscription_Manager SHALL 変更を適用し、ユーザーに通知する
4. WHEN 管理者がサブスクリプションをキャンセルする THEN THE System SHALL 即座にキャンセルし、ユーザーをFree_Planに移行する
5. WHEN 管理者が返金を処理する THEN THE Payment_Processor SHALL 返金を実行し、トランザクション記録を更新する
6. WHEN 管理者が収益レポートを表示する THEN THE System SHALL 月次収益、新規サブスクリプション、解約率、アクティブユーザー数を表示する

### 要件17: セキュリティとプライバシー

**ユーザーストーリー:** ユーザーとして、決済情報と個人情報が安全に保護されることを期待する。そうすることで、安心してサービスを利用できる。

#### 受け入れ基準

1. THE System SHALL すべての決済情報をPCI DSS準拠の方法で暗号化して保存する
2. THE System SHALL 決済処理にHTTPS接続のみを使用する
3. WHEN ユーザーが決済情報を入力する THEN THE System SHALL クレジットカード番号の全桁を保存せず、トークン化する
4. THE System SHALL ユーザーの個人情報と決済情報へのアクセスを認証されたユーザーのみに制限する
5. WHEN データ侵害が検出される THEN THE System SHALL 即座にセキュリティプロトコルを実行し、影響を受けるユーザーに通知する
6. THE System SHALL すべての決済トランザクションと管理者アクションを監査ログに記録する

### 要件18: エラーハンドリングとユーザーフィードバック

**ユーザーストーリー:** ユーザーとして、サブスクリプション操作の進行状況とエラーを理解したい。そうすることで、問題が発生したときに適切に対応できる。

#### 受け入れ基準

1. WHEN 決済処理が進行中である THEN THE System SHALL ローディングインジケーターを表示する
2. WHEN サブスクリプション操作が完了する THEN THE System SHALL 成功メッセージを表示する
3. IF 決済エラーが発生する THEN THE System SHALL ユーザーフレンドリーなエラーメッセージと解決手順を表示する
4. IF ネットワークエラーが発生する THEN THE System SHALL 再試行オプションを提供する
5. WHEN プラン制限に達する THEN THE System SHALL 明確な説明とアップグレードオプションを含む通知を表示する
6. WHEN エラーが発生する THEN THE System SHALL エラーの詳細をログに記録し、サポートチームに通知する
