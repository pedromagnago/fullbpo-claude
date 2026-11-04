import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import httpx
import finops_connect as c

PROFILE = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
class ConnectTests(unittest.TestCase):
 def test_no_plaintext_fallback(self):
  with patch.object(c,'HOME',Path(tempfile.mkdtemp())),patch.object(c.keyring,'get_keyring',return_value=MagicMock()),patch.object(c.keyring,'set_password') as save:
   with self.assertRaisesRegex(RuntimeError,'Cofre'): c.save_connection({'company':{'id':PROFILE}},'secret')
   save.assert_not_called()
 def test_path_traversal(self):
  with self.assertRaises(RuntimeError): c.profile_path('../../stolen')
 def test_transport_error_does_not_confirm_connection(self):
  with patch.object(httpx.Client,'post',side_effect=httpx.ConnectError('offline')):
   with self.assertRaisesRegex(RuntimeError,'não foi confirmada'): c.api({})
 def test_errors_never_echo_body_or_token(self):
  with patch.object(httpx.Client,'post',return_value=httpx.Response(401,json={'error':'credencial_invalida','token':'SECRET'})):
   with self.assertRaises(RuntimeError) as e: c.api({},'SECRET')
   self.assertNotIn('SECRET',str(e.exception))
 def test_export_exclusive_and_private(self):
  file=Path(tempfile.mkdtemp())/'key.json'
  with patch.object(c,'token_for',return_value='fixture'):
   c.export_api(PROFILE,file)
   self.assertEqual(json.loads(file.read_text())['token'],'fixture')
   with self.assertRaises(FileExistsError): c.export_api(PROFILE,file)
 def test_claude_config_preserved_on_collision(self):
  failed=MagicMock(returncode=1,stdout='different command')
  with patch.object(c.shutil,'which',return_value='/bin/claude'),patch.object(c.subprocess,'run',return_value=failed) as run:
   with self.assertRaisesRegex(RuntimeError,'Nenhuma configuração'): c.register_claude(PROFILE)
   self.assertFalse(any('remove' in call.args[0] for call in run.call_args_list))
 def test_mcp_catalog_and_filtered_call(self):
  async def check():
   server=c.create_mcp(PROFILE)
   tools=await server.list_tools()
   self.assertEqual({t.name for t in tools},{'finops_empresa','finops_contas','finops_movimentos','finops_titulos'})
   self.assertTrue(all(t.annotations.readOnlyHint for t in tools))
   with patch.object(c,'token_for',return_value='fixture'),patch.object(c,'api',return_value={'data':{'records':[]}}) as api:
    await server.call_tool('finops_movimentos',{'conciliado':False})
    body=api.call_args.args[0]
    self.assertEqual(body['params'],{'conciliado':False,'limit':50,'offset':0})
    json.dumps(body)
  asyncio.run(check())
 def test_doctor_requires_real_query(self):
  with patch.object(c,'token_for',return_value='fixture'),patch.object(c,'api',side_effect=[{'status':'approved'},RuntimeError('query failed')]):
   with self.assertRaisesRegex(RuntimeError,'query failed'): c.diagnose(PROFILE)

if __name__=='__main__': unittest.main()
