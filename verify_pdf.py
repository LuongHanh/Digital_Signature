import re
import sys
from cryptography import x509
from asn1crypto import cms

def extract_signature(pdf_bytes):
    """Trích xuất vùng được ký và chữ ký PKCS#7 từ PDF."""
    match = re.search(rb"/ByteRange\s*\[\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\]", pdf_bytes)
    if not match:
        raise RuntimeError("Không tìm thấy /ByteRange trong PDF.")
    a, b, c, d = map(int, match.groups())

    contents = pdf_bytes[b:c].strip(b"\x00")
    to_be_signed = pdf_bytes[:b] + pdf_bytes[c:]
    return to_be_signed, contents


def verify_signature(pdf_path, cert_path):
    """Phân tích cấu trúc chữ ký số PKCS#7 trong PDF."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    to_be_signed, der_sig = extract_signature(pdf_bytes)

    with open(cert_path, "rb") as f:
        cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data)

    # Phân tích khối PKCS#7
    try:
        pkcs7 = cms.ContentInfo.load(der_sig)
    except Exception as e:
        print("Không đọc được dữ liệu PKCS#7:", e)
        return

    if pkcs7["content_type"].native != "signed_data":
        print("Không phải kiểu SignedData.")
        return

    signed_data = pkcs7["content"]
    signer_infos = signed_data["signer_infos"]
    certs = signed_data["certificates"]

    print("Thuật toán ký:", cert.signature_algorithm_oid._name)
    print("Kích thước chữ ký:", len(der_sig), "bytes")
    print(f"PKCS#7 chứa {len(certs)} chứng chỉ và {len(signer_infos)} signer(s).")

    if certs and signer_infos:
        print("Cấu trúc chữ ký hợp lệ (có signer và certificate).")
    else:
        print("Thiếu thông tin signer hoặc certificate trong chữ ký.")

    # Hướng dẫn xác thực thực tế bằng OpenSSL
    print("\nĐể kiểm chứng thủ công, có thể dùng lệnh:")
    print("openssl cms -verify -inform DER -in signature.der -content data.bin -noverify -certfile demo_cert.pem")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Cách dùng: python verify_pdf.py <signed.pdf> <certificate.pem>")
        sys.exit(1)

    verify_signature(sys.argv[1], sys.argv[2])
