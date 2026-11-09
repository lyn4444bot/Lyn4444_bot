import telebot
import asyncio
import json
import os
import random
from chanify import Chanify
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ================= KONFIGURASI (WAJIB DIGANTI) =================
TOKEN = '9179230016:AAEjRHJNWQMRfOuL7HKUquCSymGhvqU3KYw'
CHANIFY_KEY = 'chanify_live_52d503058bb495d63237215 9d00d9fca'
ADMIN_ID = '9179230016'
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
    
    markup.add(btn_iklan)
    markup.add(btn_saldo, btn_akun)
    return markup

# --- Handler Perintah /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"saldo": 0, "total_iklan": 0}
        save_data(data)
        
    bot.reply_to(message, "Halo! Selamat datang di Lyn4444_bot.\nSilakan pilih menu di bawah ini:", reply_markup=main_menu())

# --- Handler Tombol Menu (Mendeteksi teks dari keyboard) ---
@bot.message_handler(func=lambda message: message.text in ["📺 Lihat Iklan", "💰 Cek Saldo", "👤 Info Akun"])
def handle_menu(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    # 1. Cek Saldo
    if message.text == "💰 Cek Saldo":
        saldo = data.get(user_id, {}).get("saldo", 0)
        bot.reply_to(message, f"Saldo kamu saat ini: Rp{saldo:,}")
        
    # 2. Info Akun
    elif message.text == "👤 Info Akun":
        total = data.get(user_id, {}).get("total_iklan", 0)
        bot.reply_to(message, f"👤 **Info Akun**\nID: `{user_id}`\nTotal Iklan: {total}", parse_mode='Markdown')
        
    # 3. Lihat Iklan & Dapat Hadiah
    elif message.text == "📺 Lihat Iklan":
        bot.reply_to(message, "Sedang menyiapkan iklan, mohon tunggu...")
        
        try:
            # Tampilkan Iklan Chanify
            asyncio.run(chanify.show_ad(chat_id=message.chat.id, user=message.from_user))
            
            # Kalkulasi Reward Acak
            reward = random.choice([50, 100, 200])
            data[user_id]["saldo"] += reward
            data[user_id]["total_iklan"] += 1
            save_data(data)
            
            bot.reply_to(message, f"🎉 Kamu mendapatkan **Rp{reward}** dari iklan ini!", parse_mode='Markdown')
            
            # Cek Syarat Penarikan (Minimal 50.000)
            if data[user_id]["saldo"] >= 50000:
                bot.reply_to(message, "🔥 **SALDO KAMU SUDAH MENCAPAI Rp50.000!**\n\nUntuk melakukan penarikan, kamu wajib memposting video tentang bot ini di TikTok/Instagram/YouTube.\n\nJika sudah posting, kirimkan **LINK VIDEO** kamu ke sini dengan format:\n`/klaim https://link-video-kamu.com`", parse_mode='Markdown')
                
        except Exception as e:
            bot.reply_to(message, f"❌ Gagal memuat iklan. Coba lagi nanti. (Error: {e})")

# --- Handler Perintah /klaim (Kirim Link Video) ---
@bot.message_handler(commands=['klaim'])
def claim_reward(message):
    user_id = str(message.from_user.id)
    data = load_data()
    saldo = data.get(user_id, {}).get("saldo", 0)
    
    if saldo < 50000:
        bot.reply_to(message, "❌ Saldo kamu belum mencukupi Rp50.000.")
        return
        
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "❌ Format salah. Gunakan: `/klaim link_video_kamu`", parse_mode='Markdown')
        return
        
    link_video = text_parts[1]
    
    admin_message = f"🔔 **PENARIKAN BARU**\n\nUser ID: `{user_id}`\nUsername: @{message.from_user.username}\nSaldo: Rp{saldo:,}\nLink Video: {link_video}\n\nSilakan cek video, jika valid transfer uang ke user dan kirim perintah `/selesai {user_id}` ke bot ini."
    
    bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
    bot.reply_to(message, "✅ Link video kamu sudah dikirim ke Admin. Mohon tunggu proses verifikasi maksimal 1x24 jam.")

# --- Handler Perintah /selesai (Khusus Admin) ---
@bot.message_handler(commands=['selesai'])
def finish_withdrawal(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, "❌ Kamu bukan admin!")
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
        bot.reply_to(message, f"✅ Saldo user {target_user} berhasil di-reset ke 0.")
        try:
            bot.send_message(target_user, "✅ **PENARIKAN BERHASIL!**\nAdmin sudah memproses penarikanmu. Saldo kamu telah di-reset. Terima kasih sudah mempromosikan bot!")
        except:
            pass 
    else:
        bot.reply_to(message, "❌ User tidak ditemukan.")

# --- Handler /menu ---
@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.reply_to(message, "Silakan pilih menu:", reply_markup=main_menu())

print("Bot Lyn4444_bot berjalan...")
bot.infinity_polling()
