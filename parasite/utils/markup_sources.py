from telebot.types import InputMediaPhoto, InputMediaDocument, InputMediaVideo, InputMediaAudio, InputMediaAnimation

from loader import bot

callback_datas_dashboard = (
    'faq',
    'proceeds',
    'last_button',
    'link_site',
    'monetization',
    'subscription',
    'support'

)
callback_datas_ui_faq = (
    'faq-service_info',
    'faq-payout_terms',
    'faq-calc_info',
    'faq-colab',
    'faq-reviews_guarantees',
    'faq-min_withdrawal',
    'faq-transfer_screenshot',
    'faq-hold_funds',
    'faq-invoice_payment',
    'faq-transfer_countries',
    'faq-paypal_beatstars',
    'faq-bs_wallet',
    'faq-label_payment',
    'faq-crypto_to_cash'
)
callback_datas_proceeds = [
    {
        'name': 'PayPal',
        'id': 'proceeds-paypal',
        'btn_type': 'details'
    },
    {
        'name': 'Cash App',
        'id': 'proceeds-cash_app',
        'btn_type': 'link'
    },
    {
        'name': 'Apple pay',
        'id': 'proceeds-apple_pay',
        'btn_type': 'link'
    }
    # {
    #     'name': 'Venmo',
    #     'id': 'proceeds-venmo',
    #     'btn_type': 'link'
    # },
    # {
    #     'name': 'Zelle',
    #     'id': 'proceeds-zelle',
    #     'btn_type': 'link'
    # },
    # {
    #     'name': 'Card',
    #     'id': 'proceeds-card',
    #     'btn_type': 'link'
    # },
]

callback_datas_link_site = [
    {
        'id': 'link_site-paypal_bs_sales',
        'id_inside_button': 'link_site-paypal_bs_sales-link_paypal'
    },
    {
        'id': 'link_site-bs_wallet_withdraw',
        'id_inside_button': 'link_site-bs_wallet_withdraw-instruction'
    },
    {
        'id': 'link_site-other_sites_services',
        'id_inside_button': 'link_site-other_sites_services-link_paypal'
    },
]
callback_datas_monetization = [
    {
        'id': 'monetization-youtube',
        'id_inside_button': 'monetization-youtube-link_adsense'
    },
    {
        'id': 'monetization-tiktok',
        'id_inside_button': 'monetization-tiktok-link_tiktok'
    },
]
def get_content_data(message):
    return {
        "photo": {
            "file_id": message.photo[-1].file_id if message.content_type == "photo" else None,
            "send_function": bot.send_photo,
            "send_param": "photo",
            "spoiler_param": "has_spoiler",
            "object": InputMediaPhoto
        },
        "document": {
            "file_id": message.document.file_id if message.content_type == "document" else None,
            "send_function": bot.send_document,
            "spoiler_param": None,
            "send_param": "document",
            "object": InputMediaDocument
        },
        "video": {
            "file_id": message.video.file_id if message.content_type == "video" else None,
            "send_function": bot.send_video,
            "spoiler_param": "has_spoiler",
            "send_param": "video",
            "object": InputMediaVideo
        },
        "audio": {
            "file_id": message.audio.file_id if message.content_type == "audio" else None,
            "send_function": bot.send_audio,
            "spoiler_param": None,
            "send_param": "audio",
            "object": InputMediaAudio
        },
        "animation": {
            "file_id": message.animation.file_id if message.content_type == "animation" else None,
            "send_function": bot.send_animation,
            "spoiler_param": None,
            "send_param": "animation",
            "object": InputMediaAnimation
        },
        "photo_caption_edit": {
            "file_id": message.photo[-1].file_id if message.content_type == "photo" else None,
            "show_sender_details": False
        },
        "video_caption_edit": {
            "file_id": message.video.file_id if message.content_type == "video" else None,
            "show_sender_details": False
        },
        "document_caption_edit": {
            "file_id": message.document.file_id if message.content_type == "document" else None,
            "show_sender_details": True
        },
        "audio_caption_edit": {
            "file_id": message.document.file_id if message.content_type == "document" else None,
            "show_sender_details": True
        },
        "animation_caption_edit": {
            "file_id": message.animation.file_id if message.content_type == "animation" else None,
            "show_sender_details": True
        },
        "voice_caption_edit": {
            "file_id": message.voice.file_id if message.content_type == "voice" else None,
            "show_sender_details": True
        }
    }