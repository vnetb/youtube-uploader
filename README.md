# Youtube Data APIを使用したアップロード

2024年8月アップロード直後に非公開（ロック）となる事象が発生。

Xにてサポートを依頼。

`本件についてはサードパーティのサービスを使用してYouTubeにアップロードされたことが原因となります。検証済みのサードパーティのサービス、またはYouTube経由であれば動画を再アップロードして公開することができます。`
https://x.com/TeamYouTube/status/1829322321976291786

## 検証済みのサードパーティとして
監査の実施様のレポジトリ及び、これで通ればforkして変更の上、監査へ依頼しやすくなるかと思います。

## YouTube API サービス - 監査と割り当て増加フォーム
https://support.google.com/youtube/contact/yt_api_form?sjid=15455882317745806520-AP

# 実行
`python youtube.py`

# 初回ログイン
1. 出力されるURLに別PCでアクセスしログイン
2. ログイン後localhostのアドレスに遷移するのでURLコピー
3. 実行したPCでcurlなどでアクセス

# 変更前の参考ソース
https://github.com/youtube/api-samples/blob/master/python/upload_video.py