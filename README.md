# DjangoSample
***

## データベースにテーブルを作成

* マイグレーションファイルを生成
```
docker-compose run web python manage.py makemigrations
```

* マイグレーションファイルをデータベースに反映
```
docker-compose run web python manage.py migrate
```

## 管理ユーザーを作成

* adminサイトにログインできるユーザーを作成する
```
docker-compose run web python manage.py createsuperuser
```

## 起動

* 開発用サーバの起動
```
docker-compose up
```

* `http://192.168.99.100:8000/admin`でadminサイトに入る

## 停止

* 開発用サーバの停止
```
docker-compose down
```
