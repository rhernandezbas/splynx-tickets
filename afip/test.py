import datetime
import subprocess
import base64
from lxml import etree
from zeep import Client

# ============================
# CONFIGURACIÓN
# ============================
SERVICE = "wsmtxca"  # Servicio destino
CERT = "cert_full.crt"    # Certificado de aplicación (homologación)
KEY = "private.key"  # Clave privada asociada
TRA_PATH = "TRA.xml"
CMS_PATH = "TRA.cms"
TA_PATH = "TA.xml"

# WSAA homologación
WSAA_WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
# WSMTXCA homologación
WSMTXCA_WSDL = "https://wswhomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"

CUIT = 20123456789  # ⚠️ tu CUIT real


# ============================
# 1) Crear TRA.xml
# ============================
def crear_tra(service=SERVICE, out_path=TRA_PATH):
    now = datetime.datetime.utcnow()
    gen_time = (now - datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    exp_time = (now + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")

    root = etree.Element("loginTicketRequest", version="1.0")
    header = etree.SubElement(root, "header")
    etree.SubElement(header, "uniqueId").text = str(int(now.timestamp()))
    etree.SubElement(header, "generationTime").text = gen_time
    etree.SubElement(header, "expirationTime").text = exp_time
    etree.SubElement(root, "service").text = service

    xml_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    with open(out_path, "wb") as f:
        f.write(xml_str)

    print(f"[OK] TRA generado en {out_path}")
    return out_path


# ============================
# 2) Firmar con OpenSSL (CMS)
# ============================
def firmar_tra(tra_path=TRA_PATH, cms_path=CMS_PATH, cert="cert.crt", key=KEY):
    cmd = [
        "openssl", "smime", "-sign",
        "-in", tra_path,
        "-out", cms_path,
        "-signer", cert,
        "-inkey", key,
        "-outform", "DER", "-nodetach"
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] TRA firmado en {cms_path}")
    return cms_path



# ============================
# 3) Llamar al WSAA
# ============================
def login_cms(cms_path=CMS_PATH, wsdl=WSAA_WSDL):
    client = Client(wsdl=wsdl)
    cms_bytes = open(cms_path, "rb").read()
    cms_b64 = base64.b64encode(cms_bytes).decode("utf-8")
    response = client.service.loginCms(cms_b64)
    print("[OK] LoginCms ejecutado")
    return response


# ============================
# 4) Guardar TA.xml
# ============================
def guardar_ta(response_xml, out_path=TA_PATH):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(response_xml)
    print(f"[OK] TA guardado en {out_path}")


# ============================
# 5) Obtener token y sign
# ============================
def obtener_token_sign(ta_path=TA_PATH):
    tree = etree.parse(ta_path)
    token = tree.findtext(".//token")
    sign = tree.findtext(".//sign")
    return token, sign


# ============================
# 6) Emitir factura (WSMTXCA)
# ============================
def emitir_factura_wsmtxca():
    token, sign = obtener_token_sign()
    client = Client(wsdl=WSMTXCA_WSDL)

    hoy = datetime.datetime.now().strftime("%Y-%m-%d")

    # ⚠️ En la práctica, primero deberías llamar a "consultarUltimoComprobanteAutorizado"
    # para obtener el último número y sumarle 1.
    # Acá usamos "1" como ejemplo.
    numero_comprobante = 1

    # Ejemplo de comprobante con detalle de un ítem
    comprobante = {
        "comprobanteCAERequest": {
            "id": 1,
            "fechaEmision": hoy,
            "tipoComprobante": 6,  # 6 = Factura B
            "puntoVenta": 1,
            "numeroComprobante": numero_comprobante,
            "concepto": 1,  # 1 = Productos
            "codigoDocumentoComprador": 96,  # 96 = DNI
            "numeroDocumentoComprador": 12345678,
            "importeTotal": 1210.00,
            "importeGravado": 1000.00,
            "importeIVA": 210.00,
            "importeTributos": 0.00,
            "moneda": {
                "codigoMoneda": "PES",
                "cotizacionMoneda": 1
            },
            "detalle": [
                {
                    "descripcion": "Producto de prueba",
                    "cantidad": 1,
                    "precioUnitario": 1000.00,
                    "importeTotal": 1000.00,
                    "iva": {
                        "codigo": 5,  # 5 = 21% IVA
                        "importe": 210.00
                    }
                }
            ]
        }
    }

    auth = {"token": token, "sign": sign, "cuit": CUIT}

    res = client.service.autorizarComprobante(
        authRequest=auth,
        comprobanteCAERequest=comprobante
    )

    print("Respuesta WSMTXCA:", res)
    if hasattr(res, "resultado") and res.resultado == "A":
        print(f"✅ Factura autorizada. CAE: {res.cae} (vence {res.fechaVencimientoCAE})")
    else:
        print("❌ Error:", res)


# ============================
# MAIN
# ============================
if __name__ == "__main__":
    # Paso 1: generar TRA
    crear_tra()

    # Paso 2: firmar
    firmar_tra()

    # Paso 3: loginCms
    ta_xml = login_cms()

    # Paso 4: guardar TA
    guardar_ta(ta_xml)

    # Paso 5: emitir factura
    emitir_factura_wsmtxca()
