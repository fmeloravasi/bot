import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Token do Bot (substitua pelo seu)
BOT_TOKEN = "7923626029:AAGXK7P21Jt4sy_1ZeRKW1VSj4oEh2WujW8"

# IDs dos usuários (troque pelos IDs reais do Telegram)
USUARIOS = {
    "Fernando Melo": 1464601774,
    "Marisa Melo": 1464601774,
    "Flávio Melo": 1001891279373,
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("financeiro.db")
cursor = conn.cursor()

# Criar a tabela de solicitações se não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    conta_destino TEXT,
    data TEXT,
    valor REAL,
    status TEXT
)''')
conn.commit()

# Teclado inicial para Fernando
keyboard_fernando = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_fernando.add(KeyboardButton("💰 Solicitar Pagamento"))

# Teclado para Marisa autorizar
keyboard_marisa = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_marisa.add(KeyboardButton("✅ Aprovar Pagamentos"))

# Teclado para Flávio visualizar pagamentos
keyboard_flavio = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_flavio.add(KeyboardButton("💵 Pagar Contas"))

# Comando /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id

    if user_id == USUARIOS["Fernando Melo"]:
        await message.answer("Olá Fernando! Você pode solicitar pagamentos.", reply_markup=keyboard_fernando)
    elif user_id == USUARIOS["Marisa Melo"]:
        await message.answer("Olá Marisa! Você pode aprovar solicitações.", reply_markup=keyboard_marisa)
    elif user_id == USUARIOS["Flávio Melo"]:
        await message.answer("Olá Flávio! Você pode visualizar pagamentos pendentes.", reply_markup=keyboard_flavio)
    else:
        await message.answer("Acesso negado. Você não está autorizado a usar este bot.")

# Solicitação de pagamento (Fernando)
@dp.message_handler(lambda message: message.text == "💰 Solicitar Pagamento")
async def solicitar_pagamento(message: types.Message):
    await message.answer("Envie os detalhes no formato:\n\n`Conta Destino | Data | Valor`", parse_mode="Markdown")

@dp.message_handler(lambda message: "|" in message.text)
async def receber_solicitacao(message: types.Message):
    user_id = message.from_user.id
    if user_id != USUARIOS["Fernando Melo"]:
        return

    try:
        conta, data, valor = map(str.strip, message.text.split("|"))
        valor = float(valor)

        # Salvar no banco de dados
        cursor.execute("INSERT INTO pagamentos (usuario, conta_destino, data, valor, status) VALUES (?, ?, ?, ?, ?)", 
                       ("Fernando Melo", conta, data, valor, "Pendente"))
        conn.commit()

        # Enviar para Marisa aprovar
        await bot.send_message(USUARIOS["Marisa Melo"], f"🔔 *Nova Solicitação de Pagamento*\n\n"
                                                        f"📌 *Conta:* {conta}\n"
                                                        f"📅 *Data:* {data}\n"
                                                        f"💰 *Valor:* R$ {valor:.2f}\n\n"
                                                        f"Aprovar? /aprovar_{cursor.lastrowid}", parse_mode="Markdown")
        await message.answer("Solicitação enviada para aprovação!")
    except Exception:
        await message.answer("Formato inválido. Tente novamente.")

# Aprovação de pagamento (Marisa)
@dp.message_handler(lambda message: message.text == "✅ Aprovar Pagamentos")
async def listar_pagamentos(message: types.Message):
    user_id = message.from_user.id
    if user_id != USUARIOS["Marisa Melo"]:
        return

    cursor.execute("SELECT id, conta_destino, data, valor FROM pagamentos WHERE status='Pendente'")
    pagamentos = cursor.fetchall()

    if not pagamentos:
        await message.answer("Nenhum pagamento pendente.")
        return

    for p in pagamentos:
        msg = f"🔹 ID: {p[0]}\n📌 Conta: {p[1]}\n📅 Data: {p[2]}\n💰 Valor: R$ {p[3]:.2f}\n\n"
        msg += f"Aprovar? /aprovar_{p[0]}"
        await message.answer(msg)

@dp.message_handler(lambda message: message.text.startswith("/aprovar_"))
async def aprovar_pagamento(message: types.Message):
    user_id = message.from_user.id
    if user_id != USUARIOS["Marisa Melo"]:
        return

    try:
        pagamento_id = int(message.text.split("_")[1])
        cursor.execute("UPDATE pagamentos SET status='Aprovado' WHERE id=?", (pagamento_id,))
        conn.commit()

        # Notificar Flávio
        cursor.execute("SELECT conta_destino, data, valor FROM pagamentos WHERE id=?", (pagamento_id,))
        conta, data, valor = cursor.fetchone()

        await bot.send_message(USUARIOS["Flávio Melo"], f"✅ *Pagamento Aprovado!*\n\n"
                                                        f"📌 *Conta:* {conta}\n"
                                                        f"📅 *Data:* {data}\n"
                                                        f"💰 *Valor:* R$ {valor:.2f}\n\n"
                                                        f"Marque como pago: /pagar_{pagamento_id}", parse_mode="Markdown")
        await message.answer("Pagamento aprovado e enviado para Flávio!")
    except Exception:
        await message.answer("Erro ao aprovar pagamento.")

# Confirmação de pagamento (Flávio)
@dp.message_handler(lambda message: message.text.startswith("/pagar_"))
async def pagar_pagamento(message: types.Message):
    user_id = message.from_user.id
    if user_id != USUARIOS["Flávio Melo"]:
        return

    try:
        pagamento_id = int(message.text.split("_")[1])
        cursor.execute("UPDATE pagamentos SET status='Pago' WHERE id=?", (pagamento_id,))
        conn.commit()
        await message.answer("Pagamento marcado como concluído!")
    except Exception:
        await message.answer("Erro ao processar pagamento.")

# Rodar o bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
