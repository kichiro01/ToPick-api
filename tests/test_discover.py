import datetime
import pytest
import starlette.status
from sqlalchemy.sql import text

from api.models import theme_model


#################################################################################################
#############################公開マイリスト取得のテスト#########################################################
#################################################################################################

# 【正常系】全ての公開マイリストを取得
# @pytest.mark.asyncio
# async def test_retrieve_all_public_mylists(async_client):
    
    # ケース１ デフォルトテーマを取得
    # response = await async_client.client.get("/discover/retrieve/all/")
    # assert response.status_code == starlette.status.HTTP_200_OK
    # response_obj = response.json()
    # assert len(response_obj) == 15 #テーマは全部で15個
    # # 見本として”一般”のテーマについて各カラムを確認
    # assert response_obj[0]["theme_id"] == 1
    # assert response_obj[0]["theme_type"] == "001"
    # assert response_obj[0]["title"] == "一般"
    # assert response_obj[0]["description"] == "困った時はこれ！"
    # assert response_obj[0]["image_type"] == "001"
    # assert response_obj[0]["topic"] == {"topic" : ["落ち着く空間","秋といえば？","趣味","今会いたい人","オススメのレストラン","こんな癖があります","特技","ハメを外してやってみたいこと","好きなスポーツ","これについてなら語れる！","好きな映画","家ではどんな格好？","好きなコンビニ","生まれ変わるなら男？女？","一日だけ異性になれるなら何する？","オススメの音楽","オススメのアプリ","最高のご飯のお供","自分の地元をPR!","最近のお気に入り写真","私服のこだわり","遊びでよく行くエリア","得意なモノマネ","苦手なもの","マイブーム","理想の旅行プラン","一ヶ月の休暇があるならどう使う？","一億円あったらどう使う？","私のお金の使い道・使い方","好きな匂い","ケータイのホーム画面公開！","睡眠のこだわり","休日の過ごし方","朝方？夜型？","健康のために心がけていること","好きな場所","至福のひと時","昔からの宝物","実家の独自文化","得意料理","好きなものは先食べる派？","電車の中ってどう過ごす？","こういう人が許せない","好きなブランド","犬派？猫派？","自分を動物に例えるなら","最近ハッピーだったこと","最近見た夢","起きて最初にすること","カラオケの十八番","風邪の自分なりの治療法","自分なりのゲンかつぎ","もし一つだけ魔法がつかえるなら","無人島に一つだけ持っていくなら","一日に鏡を見る回数","今週末の予定","生活の中のこだわり","携帯と財布以外の必需品","行ってみたい国","好きな芸能人","好きな季節","髪を染めたことはある？","好きな時代に行けるなら","一年前の今頃何してた？","家で一人の時何をする？","歌詞を覚えている曲は？","私って何の人で認識されてますか？","過去最高の褒め言葉"," 落ちてるお金いくらまでなら拾う？"]}
    # # discriptionがないパターンも確認
    # assert response_obj[10]["theme_id"] == 11
    # assert response_obj[10]["title"] == "暇つぶし話題30選"
    # assert response_obj[10]["description"] == None