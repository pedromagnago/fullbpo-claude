import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins/fullbpo/mcp'))
import finops_client as fc
import finops_tools as ft
import config

class BridgeTests(unittest.TestCase):
    def test_pending_is_not_discarded(self):
        pending = {'success': True, 'pending': True, 'token': 'approval', 'message': 'Nada executado'}
        with patch.object(fc, 'request', return_value=pending):
            self.assertEqual(fc.call_tool('omie_incluir_conta_pagar', {}), pending)

    def test_legacy_data_shape_preserved(self):
        with patch.object(fc, 'request', return_value={'success': True, 'data': {'ok': True}}):
            self.assertEqual(fc.call_tool('example'), {'ok': True})

    def test_live_portfolio_includes_empty_filtered_pages(self):
        with patch.object(fc, 'call_tool', side_effect=[
            {'empresas': [], 'next_offset': 100},
            {'empresas': [{'nome': 'Nova', 'company_id': 'id'}], 'next_offset': None},
        ]) as call:
            self.assertEqual(fc.empresas(), [{'nome': 'Nova', 'company_id': 'id'}])
            self.assertEqual(call.call_args.args[1]['offset'], 100)

    def test_bad_pagination_is_not_silent_partial_success(self):
        with patch.object(fc, 'call_tool', return_value={'empresas': [], 'next_offset': 0}):
            with self.assertRaises(fc.FinOpsToolError): fc.empresas()

    def test_portfolio_errors_do_not_fall_back_to_stale_file(self):
        with patch.object(fc, 'call_tool', side_effect=fc.FinOpsToolError('403')):
            with self.assertRaises(fc.FinOpsToolError): fc.empresas()

    def test_duplicate_exact_name_is_ambiguous(self):
        with patch.object(fc, 'empresas', return_value=[{'nome': 'CSSA', 'company_id': '1'}, {'nome': 'CSSA', 'company_id': '2'}]):
            with self.assertRaisesRegex(fc.FinOpsToolError, 'ambíguo'): fc.resolver_company_id('CSSA')

    def test_fantasy_name_resolves(self):
        with patch.object(fc, 'empresas', return_value=[{'nome': 'Nome legal', 'nome_fantasia': 'CSSA', 'company_id': '1'}]):
            self.assertEqual(fc.resolver_company_id('CSSA'), '1')

    def test_wrong_identity_session_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'session.json'
            p.write_text(json.dumps({'user': {'email': 'other@example.com'}, 'access_token': 'test'}))
            with patch.object(fc, '_session', None), patch.object(config, 'FINOPS_SESSION_FILE', p), patch.object(config, 'FINOPS_EMAIL', 'operator@example.com'):
                self.assertIsNone(fc._load_session())

class ToolsTests(unittest.TestCase):
    catalog = [{'name': 'manage_tarefas', 'inputSchema': {'properties': {'dry_run': {'type': 'boolean'}}}}]

    def test_catalog_dispatch_and_preview_keep_request_id(self):
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'request', return_value={'success': True}) as send:
            ft.executar('manage_tarefas', {'action': 'criar', 'tarefa_id': 'stable'})
            self.assertEqual(send.call_args.args[0]['params']['tarefa_id'], 'stable')
            self.assertTrue(send.call_args.args[0]['params']['dry_run'])

    def test_explicit_execution_is_preserved(self):
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'request') as send:
            ft.executar('manage_tarefas', {'dry_run': False})
            self.assertFalse(send.call_args.args[0]['params']['dry_run'])

    def test_unknown_tool_never_dispatched(self):
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'request') as send:
            with self.assertRaises(fc.FinOpsToolError): ft.executar('execute_sql', {})
            send.assert_not_called()

    def test_identity_cannot_be_overridden(self):
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'request') as send:
            with self.assertRaises(fc.FinOpsToolError): ft.executar('manage_tarefas', {'acting_user_id': 'pedro'})
            send.assert_not_called()

    def test_company_mismatch_is_rejected(self):
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'resolver_company_id', return_value='A'), patch.object(fc, 'request') as send:
            with self.assertRaises(fc.FinOpsToolError): ft.executar('manage_tarefas', {'company_id': 'B'}, 'A')
            send.assert_not_called()

    def test_pending_keeps_full_response(self):
        pending = {'success': True, 'pending': True, 'token': 't'}
        with patch.object(fc, 'catalogo', return_value=self.catalog), patch.object(fc, 'request', return_value=pending):
            self.assertEqual(ft.executar('manage_tarefas', {}), pending)

    def test_no_approval_without_human_confirmation(self):
        with patch.object(fc, 'request') as send:
            self.assertTrue(ft.decidir('token', True)['dry_run'])
            send.assert_not_called()

    def test_explicit_decision_uses_existing_gate(self):
        with patch.object(fc, 'request') as send:
            ft.decidir('token', False, True)
            send.assert_called_once_with({'op': 'rejeitar_pendencia', 'token': 'token'})


class DiscoveryTests(unittest.TestCase):
    def test_context_contains_installed_version(self):
        with patch.object(ft, 'executar', return_value={'success': True, 'data': {'usuario_id': 'u'}}):
            r = ft.contexto()
            self.assertEqual(r['plugin']['versao'], '1.5.0')
            self.assertEqual(r['data']['usuario_id'], 'u')

    def test_structured_permission_error_preserved(self):
        details = {'http_status': 403, 'estado': 'recusado', 'request_id': 'trace', 'proximo_passo': 'Confira o acesso'}
        with patch.object(fc, 'catalogo', return_value=ToolsTests.catalog), patch.object(fc, 'request', side_effect=fc.FinOpsToolError('negado', details)):
            r = ft.executar('manage_tarefas', {})
            self.assertFalse(r['success'])
            self.assertEqual(r['request_id'], 'trace')
            self.assertEqual(r['http_status'], 403)

    def test_registered_map_and_implantation_call_correct_server_tools(self):
        class Registry:
            functions = {}
            def tool(self):
                def register(fn):
                    self.functions[fn.__name__] = fn
                    return fn
                return register
        registry = Registry()
        ft.register(registry)
        with patch.object(ft, 'executar', return_value={'success': True}) as execute:
            registry.functions['finops_mapa']('onboarding', 'CSSA')
            execute.assert_called_once_with('finops_mapa', {'busca': 'onboarding'}, 'CSSA')
        with patch.object(ft, 'executar', return_value={'success': True}) as execute:
            registry.functions['finops_implantacao']('CSSA')
            execute.assert_called_once_with('manage_implantacao', {'action': 'consultar'}, 'CSSA')

    def test_timeout_never_retries_write(self):
        import httpx
        client = unittest.mock.MagicMock()
        client.__enter__.return_value = client
        client.post.side_effect = httpx.ReadTimeout('timeout')
        with patch.object(fc, '_access_token', return_value='test-token'), patch.object(httpx, 'Client', return_value=client):
            with self.assertRaises(fc.FinOpsToolError) as raised:
                fc.request({'tool': 'manage_implantacao', 'params': {'dry_run': False}})
            self.assertEqual(raised.exception.details['estado'], 'resultado_desconhecido')
            self.assertEqual(client.post.call_count, 1)

    def test_http_403_returns_guidance_not_tool_missing(self):
        import httpx
        client = unittest.mock.MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = httpx.Response(403, json={'error': 'forbidden_admin_only', 'request_id': 'trace'})
        with patch.object(fc, '_access_token', return_value='test-token'), patch.object(httpx, 'Client', return_value=client):
            with self.assertRaises(fc.FinOpsToolError) as raised:
                fc.request({'tool': 'comercial_onboarding', 'params': {'action': 'consultar'}})
            self.assertEqual(raised.exception.details['http_status'], 403)
            self.assertIn('finops_implantacao', raised.exception.details['proximo_passo'])

if __name__ == '__main__': unittest.main()
