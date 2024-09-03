# Youtube Data APIを使用したアップロード

2024年8月アップロード直後に非公開（ロック）となる事象が発生。

Xにてサポートを依頼。

```
本件についてはサードパーティのサービスを使用してYouTubeにアップロードされたことが原因となります。
検証済みのサードパーティのサービス、またはYouTube経由であれば動画を再アップロードして公開することができます。
```

https://x.com/TeamYouTube/status/1829322321976291786

## 検証済みのサードパーティとして
監査の実施用のレポジトリ及び、これで通ればforkして変更の上、監査へ依頼しやすくなるかと思います。

## YouTube API サービス - 監査と割り当て増加フォーム
https://support.google.com/youtube/contact/yt_api_form

- このレポジトリのソースをzipで添付した
- 割り当て量の増加は不要の旨を記述した
- 動画を公開アップロードしたい旨の記述が必要っぽい
- 無事、承認(?)されました

# 実行
```
python youtube.py --proc TextFile --mp4 MP4File
```

TextFile は Utf-16のバイナリになります。

# 初回ログイン
1. 出力されるURLに別PCでアクセスしログイン
2. ログイン後localhostのアドレスに遷移するのでURLコピー
3. 実行したPCでcurlなどでアクセス

# 変更前の参考ソース
https://github.com/youtube/api-samples/blob/master/python/upload_video.py
