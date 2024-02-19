import logging
from api.codes.report_reasons import ReportReasons
from api.cruds.mylist import getMylistById
from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from api.schemas.contact import contactRequestParam, reoprtRequestParam
import config
from sqlalchemy.ext.asyncio import AsyncSession

class MailUtils:
    logger = logging.getLogger('uvicorn')
    setting = config.Settings()
    # TODO 公式ドキュメントの下記コードだとAttributeErrorが出てしまう。毎回インスタンス生成しないで済むようにする。
    # setting = Annotated[config.Settings, Depends(config_utils.get_settings)]
    
    conf = ConnectionConfig(
        MAIL_USERNAME = setting.mail_address,
        MAIL_PASSWORD = setting.mail_application_password,
        MAIL_FROM = setting.mail_address,
        MAIL_PORT = 587,
        MAIL_SERVER = setting.mail_server,
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS = True
    )

    # ご意見・ご要望の投稿をメール通知
    async def sendContactEmail(self, body: contactRequestParam):
        message = MessageSchema(
            # TODO デバッグ時はタイトルと切り替えられるように環境変数化
            subject='【Topick】ご意見・ご要望の投稿がありました。',
            recipients=[self.setting.mail_address],
            body=self.__createContactMessageBody(body),
            subtype="html"
        )
        try:
            fm = FastMail(self.conf)
            await fm.send_message(message)
            return {"message": "Email sent successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    

    def __createContactMessageBody(self, requestBody: contactRequestParam):
        return f"<p>【ユーザーID】<br>　{requestBody.user_id}</p>\
        <p>【ご意見・ご要望】<br>　{requestBody.text}</p>"
        
    
    # 通報連絡をメール通知
    async def sendReportEmail(self, db: AsyncSession, body: reoprtRequestParam):
        message = MessageSchema(
            subject='【Topick】投稿コンテンツへの通報がありました。',
            recipients=[self.setting.mail_address],
            body= await self.__createReportMessageBody(db, body),
            subtype="html"
        )
        try:
            fm = FastMail(self.conf)
            await fm.send_message(message)
            return {"message": "Email sent successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    

    async def __createReportMessageBody(self, db: AsyncSession, requestBody: reoprtRequestParam):
        reasonCode = requestBody.reason_code
        myListId = requestBody.reported_mylist_id
        listInDb = await getMylistById(db, myListId)
        if listInDb is None: 
            self.logger.error(f"Mylist with id {myListId} not found")
            raise HTTPException(status_code=404, detail=f"Mylist with id {myListId} not found")
        topic = ''.join(['　　' + s + '<br>' for s in listInDb.getTopic()])

        return f"<p>【ユーザーID】<br>　{requestBody.user_id}</p>\
            <p>【通報理由】<br>　{ReportReasons.getTitleFromCode(reasonCode)}</p>\
            <p>【通報内容】<br>　{requestBody.report_content}</p>\
            <p>【通報対象のマイリスト】<br>\
            　作成者ID：{listInDb.user_id}<br>\
            　作成日時：{listInDb.created_at}<br>\
            　更新日時：{listInDb.updated_at}<br>\
            　マイリストID：{myListId}<br>\
            　マイリスト名：{listInDb.title}<br>\
            　トピック：<br>{topic}</p>"

    
        