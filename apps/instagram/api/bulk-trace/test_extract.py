"""Synthetic safety regressions for receiver and block tracking."""
import struct,unittest
from extract import Dex,scan,SET_METHOD,ROUTE_FIELD,ENUM
class Fixture:
 u16=Dex.u16;u32=Dex.u32;i32=Dex.i32;insns=Dex.insns
 def __init__(self,words):
  self.name='synthetic.dex';self.strings=['users/example/'];self.fields=[next(iter(ENUM)),ROUTE_FIELD]
  self.methods=[('LFixture;','example','()V'),SET_METHOD,('LUnknown;','mutate','(Ljava/lang/Object;)V')]
  self.d=b'\0'*16+struct.pack('<HHHHII',8,0,0,0,0,len(words))+struct.pack('<'+'H'*len(words),*words)
 def run(self):return scan(self,0,16)
# sget-object v1, POST; invoke-virtual {v0,v1}, set-method; const-string v2, route.
PREFIX=[0x0162,0,0x206e,1,0x0010,0x021a,0]
class TrackingTests(unittest.TestCase):
 def test_same_receiver(self):self.assertEqual(Fixture(PREFIX+[0x025b,1,0x000e]).run()[0]['method'],'POST')
 def test_other_receiver(self):self.assertEqual(Fixture(PREFIX+[0x325b,1,0x000e]).run(),[])
 def test_alias(self):self.assertEqual(len(Fixture(PREFIX+[0x0307,0x325b,1,0x000e]).run()),1)
 def test_receiver_overwrite(self):self.assertEqual(Fixture(PREFIX+[0x0012,0x025b,1,0x000e]).run(),[])
 def test_unknown_builder_call(self):self.assertEqual(Fixture(PREFIX+[0x1071,2,0,0x025b,1,0x000e]).run(),[])
 def test_branch_boundary(self):self.assertEqual(Fixture(PREFIX+[0x0138,2,0x025b,1,0x000e]).run(),[])
 def test_array_escape(self):self.assertEqual(Fixture(PREFIX+[0x004d,0x0403,0x025b,1,0x000e]).run(),[])
 def test_wide_clobber(self):
  # Builder is v1, then move-wide into v0 clobbers v1 too.
  words=[0x0262,0,0x206e,1,0x0021,0x031a,0,0x4004,0x135b,1,0x000e]
  self.assertEqual(Fixture(words).run(),[])

class RequestFieldTests(unittest.TestCase):
 def fixture(self,suffix):
  value=Fixture(PREFIX+[0x025b,1]+suffix+[0x000e])
  value.strings+=['synthetic_field','users/second/','second_field']
  value.methods.append(('LX/04x6;','AQE','(Ljava/lang/String;Ljava/lang/String;)V'))
  return value
 def test_parameter_uses_same_receiver_and_literal_key(self):
  value=self.fixture([0x031a,1,0x306e,3,0x0430])
  result=scan(value,0,16,include_request_fields=True)
  self.assertEqual(result[0]['request_fields'][0]['name'],'synthetic_field')
  self.assertEqual(result[0]['request_fields'][0]['required_status'],'unknown')
  self.assertNotIn('request_fields',scan(value,0,16)[0])
 def test_parameters_before_first_route_assignment_are_retained(self):
  value=Fixture(PREFIX+[0x031a,1,0x306e,3,0x0430,0x025b,1,0x000e])
  value.strings.append('synthetic_field')
  value.methods.append(('LX/04x6;','AQE','(Ljava/lang/String;Ljava/lang/String;)V'))
  self.assertEqual(scan(value,0,16,include_request_fields=True)[0]['request_fields'][0]['name'],'synthetic_field')
 def test_other_receiver_does_not_supply_parameters(self):
  value=self.fixture([0x031a,1,0x306e,3,0x0435])
  self.assertEqual(scan(value,0,16,include_request_fields=True)[0]['request_fields'],[])
 def test_unknown_call_stops_parameter_collection(self):
  value=self.fixture([0x1071,2,0,0x031a,1,0x306e,3,0x0430])
  self.assertEqual(scan(value,0,16,include_request_fields=True)[0]['request_fields'],[])
 def test_branch_stops_parameter_collection(self):
  value=self.fixture([0x0138,2,0x031a,1,0x306e,3,0x0430])
  self.assertEqual(scan(value,0,16,include_request_fields=True)[0]['request_fields'],[])
 def test_changed_route_does_not_inherit_previous_route_fields(self):
  value=self.fixture([0x031a,1,0x306e,3,0x0430,0x021a,2,0x025b,1,0x031a,3,0x306e,3,0x0430])
  result=scan(value,0,16,include_request_fields=True)
  self.assertEqual([f['name'] for f in result[0]['request_fields']],['synthetic_field'])
  self.assertEqual([f['name'] for f in result[-1]['request_fields']],['second_field'])

class ParserBindingTests(unittest.TestCase):
 def fixture(self,clobber=False):
  words=[0x0462,2]+([0x0412] if clobber else [])+[0x306e,3,0x0645,0x000c]+PREFIX+[0x025b,1,0x000e]
  value=Fixture(words)
  value.fields.append(('LSyntheticParser;','INSTANCE','LSyntheticParser;'))
  value.methods.append(('LX/02rr;','A03','(LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;'))
  return value
 def test_factory_parser_argument_follows_the_builder_receiver(self):
  value=self.fixture()
  result=scan(value,0,16,include_request_fields=True)
  self.assertEqual(result[0]['response_parser']['type'],'LSyntheticParser;')
  self.assertNotIn('response_parser',scan(value,0,16)[0])
 def test_clobbered_parser_argument_is_not_inferred(self):
  value=self.fixture(True)
  self.assertNotIn('response_parser',scan(value,0,16,include_request_fields=True)[0])

 def test_unknown_factory_is_not_assigned_a_parser(self):
  value=self.fixture();value.methods[3]=('LUnknown;','A03',value.methods[3][2])
  self.assertNotIn('response_parser',scan(value,0,16,include_request_fields=True)[0])

class TransportTests(unittest.TestCase):
 def fixture(self,suffix):
  words=[0x0462,2,0x3071,3,0x0540,0x000c,0x021a,0,0x025b,1]+suffix+[0x000e]
  value=Fixture(words)
  value.fields.extend([('LParser;','INSTANCE','LParser;'),('LX/04x6;','A0Y','Z'),('LX/04x6;','A0U','Z'),next(field for field,method in ENUM.items() if method=='GET')])
  value.methods.extend([('LX/0221;','A0J','(LX/02rr;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;'),
   ('LX/04x5;','A0K','()LX/02sG;'),('LX/0221;','A0T','(LX/04x5;)LX/02sG;'),
   ('LX/021R;','A0T','(LX/04x5;Z)LX/02sG;')])
  return value
 def trace(self,suffix):return scan(self.fixture(suffix),0,16,include_request_fields=True)
 def test_plain_post_form_is_bound_at_finalization(self):
  result=self.trace([0x106e,4,0])[0]['request_transport']
  self.assertEqual((result['parameter_location'],result['envelope']),('form-body','plain'))
  self.assertEqual(result['server_requiredness'],'unknown')
 def test_signing_helper_records_the_signed_envelope(self):
  self.assertEqual(self.trace([0x1071,5,0])[0]['request_transport']['envelope'],'signed')
 def test_boolean_finalizer_requires_a_known_boolean(self):
  self.assertEqual(self.trace([0x1112,0x2071,6,0x0010])[0]['request_transport']['envelope'],'signed')
  self.assertEqual(self.trace([0x0112,0x2071,6,0x0010])[0]['request_transport']['envelope'],'plain')
  self.assertNotIn('request_transport',self.trace([0x2071,6,0x0010])[0])
 def test_unknown_call_stops_transport_inference(self):
  self.assertNotIn('request_transport',self.trace([0x1071,2,0,0x106e,4,0])[0])
 def test_unknown_body_wrapper_flag_stops_transport_inference(self):
  self.assertNotIn('request_transport',self.trace([0x015c,3,0x106e,4,0])[0])
 def test_direct_signing_flag_is_preserved(self):
  self.assertEqual(self.trace([0x1112,0x015c,4,0x106e,4,0])[0]['request_transport']['envelope'],'signed')
 def test_method_override_does_not_finalize_the_old_method(self):
  result=self.trace([0x0162,5,0x206e,1,0x0010,0x106e,4,0])
  self.assertNotIn('request_transport',result[0])
  self.assertEqual((result[-1]['method'],result[-1]['request_transport']['parameter_location']),('GET','query'))
 def test_route_finalizer_binds_only_the_final_route(self):
  value=self.fixture([0x021a,1,0x2071,7,0x0020])
  value.strings.append('users/second/')
  value.methods.append(('LX/020p;','A0K','(LX/04x5;Ljava/lang/String;)LX/02sG;'))
  result=scan(value,0,16,include_request_fields=True)
  self.assertNotIn('request_transport',result[0])
  self.assertEqual(result[-1]['path'],'/users/second/')
  self.assertEqual(result[-1]['request_transport']['envelope'],'plain')
 def test_route_finalizer_with_unknown_route_does_not_finalize_old_route(self):
  value=self.fixture([0x2071,7,0x0030])
  value.methods.append(('LX/020p;','A0K','(LX/04x5;Ljava/lang/String;)LX/02sG;'))
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def helper_trace(self,helper,suffix):
  value=self.fixture(suffix);value.methods.append(helper);value.strings.append('synthetic_key')
  return scan(value,0,16,include_request_fields=True)
 def test_pagination_finalizer_adds_reviewed_literal_key(self):
  result=self.helper_trace(('LX/0064;','A0S','(LX/04x5;Ljava/lang/String;)LX/02sG;'),[0x2071,7,0x0030])[0]
  self.assertEqual(result['request_fields'][0]['name'],'max_id')
  self.assertEqual(result['request_fields'][0]['evidence']['callee'],'LX/0064;->A0S(LX/04x5;Ljava/lang/String;)LX/02sG;')
  self.assertEqual(result['request_fields'][0]['evidence']['forwarded_setter'],'LX/04x6;->A0F(Ljava/lang/String;Ljava/lang/String;)V')
  self.assertEqual(result['request_fields'][0]['client_presence'],'omitted-if-null')
  self.assertEqual(result['request_transport']['envelope'],'plain')
 def test_string_parameter_finalizers_preserve_or_set_envelope(self):
  for helper,envelope in [(('LX/0465;','A0N','(LX/04x5;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'),'plain'),(('LX/0225;','A0R','(LX/04x5;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'),'signed')]:
   result=self.helper_trace(helper,[0x011a,1,0x3071,7,0x0310])[0]
   self.assertEqual(result['request_fields'][0]['name'],'synthetic_key')
   self.assertEqual(result['request_transport']['envelope'],envelope)
 def test_parameter_flag_finalizer_requires_known_flag(self):
  helper=('LX/0221;','A0V','(LX/04x5;Ljava/lang/String;Ljava/lang/String;Z)LX/02sG;')
  for flag,envelope in [([0x1412],'signed'),([0x0412],'plain'),([],None)]:
   result=self.helper_trace(helper,[0x021a,1]+flag+[0x4071,7,0x4320])[0]
   self.assertEqual(result['request_fields'][0]['name'],'synthetic_key')
   self.assertEqual(result.get('request_transport',{}).get('envelope'),envelope)
 def test_callback_finalizer_uses_parameter_after_callback_argument(self):
  helper=('LX/0221;','A0U','(LX/04x5;LX/05BI;Ljava/lang/String;Ljava/lang/String;)LX/02sG;')
  result=self.helper_trace(helper,[0x021a,1,0x4071,7,0x3210])[0]
  self.assertEqual(result['request_fields'][0]['name'],'synthetic_key')
  self.assertEqual(result['request_transport']['envelope'],'plain')
 def test_signed_route_finalizer_detaches_old_route(self):
  value=self.fixture([0x021a,1,0x2071,7,0x0020]);value.methods.append(('LX/0224;','A0P','(LX/04x5;Ljava/lang/String;)LX/02sG;'));value.strings.append('users/second/')
  result=scan(value,0,16,include_request_fields=True)
  self.assertNotIn('request_transport',result[0])
  self.assertEqual(result[-1]['path'],'/users/second/')
  self.assertEqual(result[-1]['request_transport']['envelope'],'signed')
 def test_object_string_helper_retains_transport_and_records_conversion(self):
  value=self.fixture([0x021a,1,0x3071,7,0x0230,0x106e,4,0])
  value.strings.append('synthetic_key')
  value.methods.append(('LX/021X;','A1L','(LX/04x6;Ljava/lang/Object;Ljava/lang/String;)V'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual(result['request_fields'][0]['name'],'synthetic_key')
  self.assertEqual(result['request_fields'][0]['client_serialization'],'object-toString-then-string-value')
  self.assertEqual(result['request_transport']['envelope'],'plain')
 def test_builder_toString_receiver_invalidates_transport_tracking(self):
  value=self.fixture([0x021a,1,0x3071,7,0x0200,0x106e,4,0])
  value.strings.append('synthetic_key')
  value.methods.append(('LX/021X;','A1L','(LX/04x6;Ljava/lang/Object;Ljava/lang/String;)V'))
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def test_control_flow_boundary_stops_transport_inference(self):
  self.assertNotIn('request_transport',self.trace([0x0138,2,0x106e,4,0])[0])
class ParameterHelperTests(unittest.TestCase):
 fixture = TransportTests.fixture
 def helper_fixture(self,helper,suffix):
  value=self.fixture(suffix);value.methods.append(helper);value.strings.extend(['literal_key','next/route/'])
  return value
 def test_timezone_helper_adds_two_fields_and_keeps_finalization(self):
  value=self.helper_fixture(('LX/0586;','A1M','(LX/04x6;Ljava/lang/String;Ljava/lang/String;)V'),[0x011a,1,0x3071,7,0x0310,0x106e,4,0])
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual([f['name'] for f in result['request_fields']],['literal_key','timezone_offset'])
  self.assertEqual(result['request_fields'][1]['client_serialization'],'long-to-string')
  self.assertEqual(result['request_transport']['envelope'],'plain')
 def test_primitive_helper_keeps_logical_type_without_values(self):
  for helper,logical in [(('LX/0BY8;','A1T','(LX/04x6;Ljava/lang/String;I)V'),'integer'),(('LX/0BY8;','A1S','(LX/04x6;Ljava/lang/String;D)V'),'number')]:
   value=self.helper_fixture(helper,[0x011a,1,0x4071,7,0x3210,0x106e,4,0])
   field=scan(value,0,16,include_request_fields=True)[0]['request_fields'][0]
   self.assertEqual(field['logical_type'],logical)
   self.assertNotIn('value',field)
 def test_context_helper_uses_second_argument_as_receiver(self):
  value=self.helper_fixture(('LX/0227;','A0v','(Landroid/content/Context;LX/04x6;Ljava/lang/String;Ljava/lang/String;)V'),[0x021a,1,0x4071,7,0x3206,0x106e,4,0])
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual([f['name'] for f in result['request_fields']],['literal_key','device_id','guid'])
  self.assertIn('request_transport',result)
 def test_context_builder_alias_invalidates_tracking(self):
  value=self.helper_fixture(('LX/0227;','A0v','(Landroid/content/Context;LX/04x6;Ljava/lang/String;Ljava/lang/String;)V'),[0x021a,1,0x4071,7,0x3200,0x106e,4,0])
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def test_route_helper_does_not_attach_new_fields_or_transport_to_old_route(self):
  value=self.helper_fixture(('LX/0C87;','A1M','(LX/04x6;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V'),[0x011a,2,0x4071,7,0x3210,0x106e,4,0])
  result=scan(value,0,16,include_request_fields=True)
  self.assertNotIn('request_transport',result[0]);self.assertEqual(result[0]['request_fields'],[])
  self.assertEqual(result[-1]['path'],'/next/route/')
  self.assertEqual([f['name'] for f in result[-1]['request_fields']],['media_id','fb_auth_token'])
 def test_unknown_route_helper_argument_never_finalizes_old_route(self):
  value=self.helper_fixture(('LX/0222;','A1P','(LX/04x6;Ljava/lang/String;Ljava/lang/String;)V'),[0x3071,7,0x0430,0x106e,4,0])
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def test_helper_nonbuilder_return_cannot_be_used_as_request_receiver(self):
  value=self.helper_fixture(('LX/021X;','A0R','(LX/04x6;LX/05Dd;Ljava/lang/String;Ljava/lang/String;)LX/02df;'),[0x021a,1,0x4071,7,0x3260,0x000c,0x106e,4,0])
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def test_unreviewed_descriptor_is_not_treated_as_a_parameter_helper(self):
  value=self.helper_fixture(('LX/0586;','A1M','(LX/04x6;Ljava/lang/String;I)V'),[0x011a,1,0x3071,7,0x0310,0x106e,4,0])
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])

class RootPathEncodingTests(unittest.TestCase):
 def fixture(self,suffix):
  value=TransportTests.fixture(self,suffix)
  value.fields.append(('LX/04x6;','A0N','Z'))
  return value
 def test_root_path_flag_preserves_encoding_without_inventing_a_default_base_path(self):
  for flag,expected in [(0x1112,True),(0x0112,False)]:
   value=self.fixture([flag,0x015c,6,0x106e,4,0])
   transport=scan(value,0,16,include_request_fields=True)[0]['request_transport']
   self.assertEqual(transport['root_path_override'],expected)
   self.assertEqual(transport['parameter_location'],'form-body')
   self.assertNotIn('base_path',transport)
 def test_unknown_root_flag_stops_inference(self):
  self.assertNotIn('request_transport',scan(self.fixture([0x015c,6,0x106e,4,0]),0,16,include_request_fields=True)[0])

class GzipBodyTests(unittest.TestCase):
 def test_known_gzip_flag_preserves_form_encoding_and_signing_separately(self):
  for finalizer,envelope in [(4,'plain'),(5,'signed')]:
   value=TransportTests.fixture(self,[0x1112,0x015c,3,0x1071,finalizer,0])
   transport=scan(value,0,16,include_request_fields=True)[0]['request_transport']
   self.assertEqual(transport['content_encoding'],'gzip')
   self.assertEqual(transport['envelope'],envelope)
   self.assertEqual(transport['content_type'],'application/x-www-form-urlencoded; charset=UTF-8')
 def test_false_gzip_flag_and_get_do_not_claim_content_encoding(self):
  for suffix in [[0x0112,0x015c,3,0x106e,4,0],[0x1112,0x015c,3,0x0162,5,0x206e,1,0x0010,0x106e,4,0]]:
   result=scan(TransportTests.fixture(self,suffix),0,16,include_request_fields=True)
   self.assertNotIn('content_encoding',result[-1]['request_transport'])
 def test_phone_id_finalizer_requires_known_compression_flag(self):
  for words,expected in [([0x1412],'gzip'),([0x0412],None),([],False)]:
   value=TransportTests.fixture(self,[0x021a,1]+words+[0x5471,7,0x3260])
   value.strings.append('literal_key')
   value.methods.append(('LX/0o8B;','A01','(LX/04x5;LX/05Dd;Ljava/lang/String;Ljava/lang/String;Z)LX/02sG;'))
   result=scan(value,0,16,include_request_fields=True)[0]
   self.assertEqual({field['name'] for field in result['request_fields']},{'phone_id','literal_key'})
   if expected is False:self.assertNotIn('request_transport',result)
   else:self.assertEqual(result['request_transport'].get('content_encoding'),expected)
 def test_boost_finalizer_adds_parameters_without_claiming_success(self):
  value=TransportTests.fixture(self,[0x5471,7,0x3250])
  value.methods.append(('LX/0nRB;','A00','(LX/04x5;LX/0nRB;LX/05BI;Ljava/lang/String;Ljava/lang/String;)V'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual([field['name'] for field in result['request_fields']],['flow_id','boosted_id'])
  self.assertEqual(result['request_transport']['envelope'],'plain')
  self.assertFalse(result['dispatch_verified'])

class ReviewedCacheConfigurationTests(unittest.TestCase):
 def test_cache_fields_preserve_encoding_but_do_not_claim_dispatch_or_export_values(self):
  for field,opcode in [('A0C',0x5b),('A09',0x5b),('A00',0x5a),('A01',0x5a)]:
   descriptor='Ljava/lang/String;' if field=='A0C' else 'Ljava/lang/Integer;' if field=='A09' else 'J'
   value=TransportTests.fixture(self,[0x011a,1,0x0100|opcode,6,0x106e,4,0])
   value.strings.append('synthetic-private-cache-key')
   value.fields.append(('LX/04x6;',field,descriptor))
   transport=scan(value,0,16,include_request_fields=True)[0]['request_transport']
   self.assertEqual(transport['parameter_location'],'form-body')
   self.assertIn('unverified',transport['client_policy_status'])
   self.assertEqual(transport['client_policy_overrides'][0]['evidence']['field'],'LX/04x6;->'+field+descriptor)
   self.assertNotIn('synthetic-private-cache-key',str(transport))
 def test_unreviewed_cache_like_field_still_blocks_encoding(self):
  value=TransportTests.fixture(self,[0x015b,6,0x106e,4,0])
  value.fields.append(('LX/04x6;','A0C','Ljava/lang/Object;'))
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])
 def test_assigning_tracked_builder_as_cache_value_invalidates_tracking(self):
  value=TransportTests.fixture(self,[0x005b,6,0x106e,4,0])
  value.fields.append(('LX/04x6;','A0C','Ljava/lang/String;'))
  self.assertNotIn('request_transport',scan(value,0,16,include_request_fields=True)[0])

class AdditionalParameterHelperTests(unittest.TestCase):
 def test_phone_id_helper_tracks_second_argument_and_both_context_aliases(self):
  helper=('LX/0221;','A1L','(LX/02dl;LX/04x6;LX/02df;)V')
  for arguments,expected in [(0x506,True),(0x500,False),(0x006,False)]:
   value=TransportTests.fixture(self,[0x3071,7,arguments,0x106e,4,0]);value.methods.append(helper)
   result=scan(value,0,16,include_request_fields=True)[0]
   self.assertEqual('request_transport' in result,expected)
   if expected:self.assertEqual(result['request_fields'][0]['name'],'phone_id')
 def test_device_id_helper_records_only_literal_key(self):
  value=TransportTests.fixture(self,[0x2071,7,0x0006,0x106e,4,0])
  value.methods.append(('LX/0225;','A18','(Landroid/content/Context;LX/04x6;)V'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual([field['name'] for field in result['request_fields']],['device_id'])
  self.assertIn('request_transport',result)
 def test_messaging_destinations_stays_conditional(self):
  value=TransportTests.fixture(self,[0x2071,7,0x0010,0x106e,4,0])
  value.methods.append(('LX/0C9W;','A1Q','(LX/04x6;Ljava/lang/String;)V'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual(result['request_fields'][0]['client_presence'],'omitted-if-null-or-blank')
  self.assertEqual(result['request_fields'][0]['required_status'],'unknown')
  self.assertIn('request_transport',result)
 def test_user_journey_instance_helper_preserves_conditional_field(self):
  value=TransportTests.fixture(self,[0x406e,7,0x3506,0x106e,4,0])
  value.methods.append(('LX/03oc;','A00','(LX/04x6;Lcom/instagram/common/session/UserSession;Ljava/lang/String;)LX/0Jaf;'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual(result['request_fields'][0]['name'],'user_journey')
  self.assertEqual(result['request_fields'][0]['client_presence'],'conditional-on-feature-and-serialized-journey')
  self.assertIn('request_transport',result)
 def test_audio_page_helper_recovers_branch_keys_without_enabling_num_clips(self):
  value=TransportTests.fixture(self,[0x4071,7,0x3506,0x106e,4,0])
  value.methods.append(('LX/0Sie;','A03','(LX/0CqC;LX/04x6;Lcom/instagram/clips/audio/model/AudioPageAssetModel;Ljava/lang/String;)V'))
  result=scan(value,0,16,include_request_fields=True)[0]
  self.assertEqual({field['name'] for field in result['request_fields']},{
   'music_canonical_id','music_canonical_segment_id','referrer_media_id',
   'audio_asset_id','audio_cluster_id','original_sound_audio_asset_id','max_id','tab_type'})
  # A03 passes false for A02's include-count argument; it cannot emit num_clips.
  self.assertNotIn('num_clips',[field['name'] for field in result['request_fields']])
  self.assertTrue(all(field['required_status']=='unknown' for field in result['request_fields']))
  self.assertIn('request_transport',result)

if __name__=='__main__':unittest.main()
