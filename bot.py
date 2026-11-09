import telebot
import asyncio
import json
import os
import random
from chanify import Chanify
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ================= KONFIGURASI (WAJIB DIGANTI) =================
TOKEN = '9179230016:AAECtFXG8ZJ9YZLV4nd4d8WDW_Cm5aT2yRc'
CHANIFY_KEY = 'chanify_live_52d503058bb495d632372159d00d9fca'
ADMIN_ID = '9228257333' # ID angka, bukan username
# ===============================================================

DB_FILE = "users.json"
bot = telebot.TeleBot(TOKEN)
chanify = Chanify(CHANIFY_KEY)

# --- Fungsi Database Sederhana ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Menu Utama (Tombol Permanen di Bawah) ---
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_iklan = KeyboardButton("📺 Lihat Iklan")
    btn_saldo = KeyboardButton("💰 Cek Saldo")
    btn_akun = KeyboardButton("👤 Info Akun")
    btn_ref = KeyboardButton("🎁 Undang Teman")
    
    markup.add(btn_iklan)
    markup.add(btn_saldo, btn_akun)
    markup.add(btn_ref)
    return markup

# --- Handler Perintah /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    # Cek apakah pengguna baru mendaftar
    if user_id not in data:
        # Fitur Referral: Cek apakah dia masuk dari link undangan teman
        args = message.text.split()
        referrer_id = None
        if len(args) > 1:
            referrer_id = args[1]
            
        data[user_id] = {
            "saldo": 0, 
            "total_iklan": 0,
            "total_ref": 0,
            "referrer": referrer_id
        }
        
        # Beri bonus ke pengundang
        if referrer_id and referrer_id in data:
            data[referrer_id]["saldo"] += 500
            data[referrer_id]["total_ref"] += 1
            try:
                bot.send_message(referrer_id, "🎉 Ada teman baru yang bergabung lewat link kamu! Saldo kamu bertambah Rp500.")
            except:
                pass
                
        save_data(data)
        
    bot.reply_to(message, "Halo! Selamat datang di **Lyn4444_bot**.\n\nKlik tombol **📺 Lihat Iklan** untuk mulai menghasilkan uang receh. Kumpulkan hingga Rp50.000 dan tukarkan dengan video promosi!", parse_mode='Markdown', reply_markup=main_menu())

# --- Handler Tombol Menu (Mendeteksi teks dari keyboard) ---
@bot.message_handler(func=lambda message: message.text in ["📺 Lihat Iklan", "💰 Cek Saldo", "👤 Info Akun", "🎁 Undang Teman"])
def handle_menu(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    # 1. Cek Saldo
    if message.text == "💰 Cek Saldo":
        saldo = data.get(user_id, {}).get("saldo", 0)
        bot.reply_to(message, f"💰 **Saldo Kamu:** Rp{saldo:,}\n\nMinimal penarikan adalah Rp50.000.", parse_mode='Markdown')
        
    # 2. Info Akun & Link Referral
    elif message.text == "👤 Info Akun":
        total_iklan = data.get(user_id, {}).get("total_iklan", 0)
        total_ref = data.get(user_id, {}).get("total_ref", 0)
        ref_link = f"https://t.me/Lyn4444_bot?start={user_id}"
        
        text = (f"👤 **INFO AKUN**\n\n"
                f"🆔 ID: `{user_id}`\n"
                f"📺 Total Iklan: {total_iklan}\n"
                f"👥 Teman Diundang: {total_ref}\n\n"
                f"🔗 **Link Undangan Kamu:**\n`{ref_link}`\n"
                f"*(Bagikan link ini, jika ada yang join kamu dapat Rp500!)*")
        bot.reply_to(message, text, parse_mode='Markdown')
        
    # 3. Undang Teman
    elif message.text == "🎁 Undang Teman":
        ref_link = f"https://t.me/Lyn4444_bot?start={user_id}"
        text = (f"🎁 **UNDANG TEMAN**\n\n"
                f"Dapatkan **Rp500** untuk setiap teman yang bergabung menggunakan link kamu!\n\n"
                f"🔗 **Link Kamu:**\n`{ref_link}`")
        bot.reply_to(message, text, parse_mode='Markdown')

    # 4. Lihat Iklan & Dapat Hadiah
    elif message.text == "📺 Lihat Iklan":
        bot.reply_to(message, "⏳ Sedang menyiapkan iklan, mohon tunggu...")
        
        try:
            # Tampilkan Iklan Chanify
            asyncio.run(chanify.show_ad(chat_id=message.chat.id, user=message.from_user))
            
            # Kalkulasi Reward Acak
            reward = random.choice([50, 100, 200])
            data[user_id]["saldo"] += reward
            data[user_id]["total_iklan"] += 1
            save_data(data)
            
            bot.reply_to(message, f"🎉 Kamu mendapatkan **Rp{reward}** dari iklan ini!\nKetik /menu atau klik tombol 💰 Cek Saldo untuk melihat total saldomu.", parse_mode='Markdown')
            
            # Cek Syarat Penarikan
            if data[user_id]["saldo"] >= 50000:
                bot.reply_to(message, "🔥 **SALDO KAMU SUDAH MENCAPAI Rp50.000!**\n\nUntuk melakukan penarikan, kamu wajib memposting video tentang bot ini di TikTok/Instagram/YouTube.\n\nJika sudah posting, kirimkan **LINK VIDEO** kamu ke sini dengan format:\n`/klaim https://link-video-kamu.com`", parse_mode='Markdown')
                
        except Exception as e:
            bot.reply_to(message, f"❌ Gagal memuat iklan. Coba lagi nanti.\n(Error: {e})")

# --- Handler Perintah /klaim (Kirim Link Video) ---
@bot.message_handler(commands=['klaim'])
def claim_reward(message):
    user_id = str(message.from_user.id)
    data = load_data()
    saldo = data.get(user_id, {}).get("saldo", 0)
    
    if saldo < 50000:
        bot.reply_to(message, f"❌ Saldo kamu belum mencukupi Rp50.000. Saldo kamu saat ini: Rp{saldo:,}")
        return
        
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "❌ Format salah. Gunakan: `/klaim link_video_kamu`", parse_mode='Markdown')
        return
        
    link_video = text_parts[1]
    
    admin_message = (f"🔔 **PENARIKAN BARU**\n\n"
                     f"User ID: `{user_id}`\n"
                     f"Username: @{message.from_user.username}\n"
                     f"Saldo: Rp{saldo:,}\n"
                     f"Link Video: {link_video}\n\n"
                     f"Jika valid, transfer uang ke user dan kirim perintah `/selesai {user_id}` ke bot ini.")
    
    bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
    bot.reply_to(message, "✅ Link video kamu sudah dikirim ke Admin. Mohon tunggu proses verifikasi maksimal 1x24 jam.")

# --- ADMIN COMMANDS ---

# Perintah /selesai (Mereset saldo setelah dibayar)
@bot.message_handler(commands=['selesai'])
def finish_withdrawal(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
        
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "❌ Format: `/selesai user_id`", parse_mode='Markdown')
        return
        
    target_user = text_parts[1]
    data = load_data()
    
    if target_user in data:
        data[target_user]["saldo"] = 0 
        save_data(data)
        bot.reply_to(message, f"✅ Saldo user {target_user} berhasil di-reset ke Rp0.")
        try:
            bot.send_message(target_user, "✅ **PENARIKAN BERHASIL!**\nAdmin sudah memproses penarikanmu. Saldo kamu telah di-reset. Terima kasih sudah mempromosikan bot!")
        except:
            pass 
    else:
        bot.reply_to(message, "❌ User tidak ditemukan.")

# Perintah /stats (Melihat total pengguna)
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    data = load_data()
    total_users = len(data)
    bot.reply_to(message, f"📊 **STATISTIK BOT**\n\nTotal Pengguna: {total_users}", parse_mode='Markdown')

# Perintah /broadcast (Kirim pesan ke semua pengguna)
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "❌ Format: `/broadcast pesan kamu`", parse_mode='Markdown')
        return
        
    pesan = text_parts[1]
    data = load_data()
    sukses = 0
    gagal = 0
    
    bot.reply_to(message, "⏳ Sedang mengirim pesan ke semua pengguna...")
    
    for user_id in data.keys():
        try:
            bot.send_message(user_id, pesan, parse_mode='Markdown')
            sukses += 1
        except:
            gagal += 1
            
    bot.reply_to(message, f"✅ Broadcast selesai!\nSukses: {sukses}\nGagal: {gagal}")

# --- Handler /menu ---
@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.reply_to(message, "Silakan pilih menu:", reply_markup=main_menu())

print("Bot Lyn4444_bot berjalan...")
# Gunakan parameter long_polling untuk mencegah bot diam (freeze)
bot.infinity_polling(timeout=10, long_polling_timeout=5)
