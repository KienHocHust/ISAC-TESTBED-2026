def encode_payload(text, packet_len=64):
    data = text.encode('utf-8')
    if not 1 <= len(data) <= packet_len:
        raise ValueError(f'Câu phát dài {len(data)} byte UTF-8; cần từ 1 đến {packet_len} byte.')
    return data.ljust(packet_len, b' ')
