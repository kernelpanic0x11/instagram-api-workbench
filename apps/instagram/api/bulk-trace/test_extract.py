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
if __name__=='__main__':unittest.main()
