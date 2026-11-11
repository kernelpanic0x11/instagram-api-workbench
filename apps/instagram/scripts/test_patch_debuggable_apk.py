"""Synthetic regression tests for the compiled-manifest APK patcher."""
import importlib.util
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).with_name('patch-debuggable-apk.py')
SPEC = importlib.util.spec_from_file_location('patch_debuggable_apk', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def chunk(chunk_type, header_size, body):
    return struct.pack('<HHI', chunk_type, header_size, header_size + len(body)) + body


def utf8_pool(strings):
    values = []
    offsets = []
    for value in strings:
        offsets.append(sum(map(len, values)))
        payload = value.encode()
        values.append(bytes((len(value), len(payload))) + payload + b'\0')
    body = b''.join(values)
    body += b'\0' * ((-len(body)) % 4)
    header_size = 28
    strings_start = header_size + 4 * len(strings)
    size = strings_start + len(body)
    return (
        struct.pack('<HHIIIIII', MODULE.RES_STRING_POOL_TYPE, header_size, size, len(strings), 0, MODULE.UTF8_FLAG, strings_start, 0)
        + struct.pack(f'<{len(offsets)}I', *offsets)
        + body
    )


def start_element(element_index, attributes):
    node = struct.pack('<II', 1, MODULE.NO_INDEX)
    attr_ext = struct.pack('<IIHHHHHH', MODULE.NO_INDEX, element_index, 20, 20, len(attributes), 0, 0, 0)
    attrs = b''.join(struct.pack('<IIIHBBI', MODULE.NO_INDEX, *attribute) for attribute in attributes)
    return struct.pack('<HHI', MODULE.RES_XML_START_ELEMENT_TYPE, 16, 16 + len(attr_ext) + len(attrs)) + node + attr_ext + attrs


def manifest(debuggable=0):
    string_pool = chunk(MODULE.RES_STRING_POOL_TYPE, 8, b'')
    resource_map = chunk(
        MODULE.RES_XML_RESOURCE_MAP_TYPE,
        8,
        struct.pack('<II', 0x01010000, MODULE.ANDROID_DEBUGGABLE),
    )
    node = struct.pack('<II', 1, 0xFFFFFFFF)
    attr_ext = struct.pack('<IIHHHHHH', 0xFFFFFFFF, 0, 20, 20, 1, 0, 0, 0)
    attribute = struct.pack(
        '<IIIHBBI',
        0xFFFFFFFF,
        1,
        0xFFFFFFFF,
        8,
        0,
        MODULE.TYPE_INT_BOOLEAN,
        debuggable,
    )
    start_element = (
        struct.pack('<HHI', MODULE.RES_XML_START_ELEMENT_TYPE, 16, 16 + len(attr_ext) + len(attribute))
        + node
        + attr_ext
        + attribute
    )
    body = string_pool + resource_map + start_element
    return struct.pack('<HHI', 0x0003, 8, 8 + len(body)) + body


def clone_manifest():
    strings = [
        'manifest', 'package', 'com.instagram.android', 'application', 'debuggable',
        'provider', 'authorities', 'com.instagram.android.provider.example',
        'permission', 'name', 'com.instagram.android.permission.EXAMPLE',
        'activity', 'com.instagram.android.activity.MainTabActivity', 'label',
        'com.instagram.contentprovider.SharedName',
        'activity-alias', 'targetActivity',
        'com.instagram.ui.splash.alias.IgSplashAliasSmokeTestActivity',
        'com.instagram.mainactivity.InstagramMainActivity',
    ]
    pool = utf8_pool(strings)
    resource_map = chunk(
        MODULE.RES_XML_RESOURCE_MAP_TYPE,
        8,
        struct.pack('<IIIII', 0, 0, 0, 0, MODULE.ANDROID_DEBUGGABLE),
    )
    string_attr = lambda name, value: (name, value, 8, 0, MODULE.TYPE_STRING, value)
    bool_attr = lambda name, value: (name, MODULE.NO_INDEX, 8, 0, MODULE.TYPE_INT_BOOLEAN, value)
    reference_attr = lambda name, value: (name, MODULE.NO_INDEX, 8, 0, MODULE.TYPE_REFERENCE, value)
    elements = b''.join([
        start_element(0, [string_attr(1, 2)]),
        start_element(3, [bool_attr(4, 0), reference_attr(13, 0x7F130009)]),
        start_element(5, [string_attr(6, 7)]),
        start_element(5, [string_attr(9, 14), string_attr(6, 14)]),
        start_element(8, [string_attr(9, 10)]),
        start_element(11, [string_attr(9, 12)]),
        start_element(11, [string_attr(9, 17)]),
        start_element(15, [string_attr(9, 12), string_attr(16, 18)]),
    ])
    body = pool + resource_map + elements
    return struct.pack('<HHI', 0x0003, 8, 8 + len(body)) + body


def attribute_values(data):
    strings = MODULE.read_string_pool(data)['values']
    result = []
    xml_header_size = struct.unpack_from('<H', data, 2)[0]
    for offset, chunk_type, header_size, _ in MODULE.chunks(data, xml_header_size):
        if chunk_type != MODULE.RES_XML_START_ELEMENT_TYPE:
            continue
        attr_ext = offset + header_size
        element = strings[struct.unpack_from('<I', data, attr_ext + 4)[0]]
        attribute_start, attribute_size, attribute_count = struct.unpack_from('<HHH', data, attr_ext + 8)
        for index in range(attribute_count):
            attribute = attr_ext + attribute_start + index * attribute_size
            name_index, raw_index = struct.unpack_from('<II', data, attribute + 4)
            _, _, value_type, value_data = struct.unpack_from('<HBBI', data, attribute + 12)
            value_index = raw_index if raw_index != MODULE.NO_INDEX else value_data if value_type == MODULE.TYPE_STRING else None
            if value_index is not None:
                result.append((element, strings[name_index], strings[value_index]))
    return result


class PatchDebuggableApkTests(unittest.TestCase):
    def test_patches_only_compiled_boolean_value(self):
        original = manifest()
        patched = MODULE.patch_manifest(original)
        self.assertEqual(len(patched), len(original))
        differences = [index for index, pair in enumerate(zip(original, patched)) if pair[0] != pair[1]]
        self.assertEqual(differences, [len(original) - 4, len(original) - 3, len(original) - 2, len(original) - 1])
        self.assertEqual(patched[-4:], b'\xff\xff\xff\xff')

    def test_rejects_already_debuggable_manifest(self):
        with self.assertRaisesRegex(MODULE.PatchError, 'already true'):
            MODULE.patch_manifest(manifest(0xFFFFFFFF))

    def test_clone_renames_install_identity_but_not_component_class(self):
        patched = MODULE.patch_manifest(clone_manifest(), 'com.instagram.android.inspect')
        values = MODULE.read_string_pool(patched)['values']
        attributes = attribute_values(patched)
        self.assertIn('com.instagram.android.inspect', values)
        self.assertIn('com.instagram.android.inspect.provider.example', values)
        self.assertIn('com.instagram.android.inspect.permission.EXAMPLE', values)
        self.assertIn('com.instagram.android.activity.MainTabActivity', values)
        self.assertIn('com.instagram.contentprovider.SharedName', values)
        self.assertIn('com.instagram.contentprovider.SharedName.inspect', values)
        self.assertIn(('provider', 'name', 'com.instagram.contentprovider.SharedName'), attributes)
        self.assertIn(('provider', 'authorities', 'com.instagram.contentprovider.SharedName.inspect'), attributes)

    def test_label_replaces_application_resource_with_direct_string(self):
        patched = MODULE.patch_manifest(clone_manifest(), enable_debuggable=True, app_label='Evil Instagram')
        self.assertIn(('application', 'label', 'Evil Instagram'), attribute_values(patched))

    def test_launcher_reuses_declared_activity_and_retargets_primary_alias(self):
        patched = MODULE.patch_manifest(
            clone_manifest(),
            enable_debuggable=True,
            launcher_class='com.evilinstagram.EvilLaunchActivity',
        )
        attributes = attribute_values(patched)
        self.assertIn(('activity', 'name', 'com.evilinstagram.EvilLaunchActivity'), attributes)
        self.assertIn(('activity-alias', 'targetActivity', 'com.evilinstagram.EvilLaunchActivity'), attributes)
        self.assertIn(('activity-alias', 'name', 'com.instagram.android.activity.MainTabActivity'), attributes)

    def test_apk_patch_preserves_payload_and_removes_v1_signatures(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.apk'
            destination = Path(directory) / 'patched.apk'
            with zipfile.ZipFile(source, 'w') as apk:
                apk.writestr('AndroidManifest.xml', manifest())
                apk.writestr('classes.dex', b'unchanged')
                apk.writestr('META-INF/CERT.RSA', b'old signature')
            MODULE.patch_apk(source, destination)
            with zipfile.ZipFile(destination) as apk:
                self.assertEqual(apk.read('classes.dex'), b'unchanged')
                self.assertNotIn('META-INF/CERT.RSA', apk.namelist())
                self.assertEqual(apk.read('AndroidManifest.xml')[-4:], b'\xff\xff\xff\xff')

    def test_refuses_to_overwrite_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.apk'
            destination = Path(directory) / 'patched.apk'
            source.write_bytes(b'input')
            destination.write_bytes(b'keep')
            with self.assertRaisesRegex(MODULE.PatchError, 'refusing to overwrite'):
                MODULE.patch_apk(source, destination)
            self.assertEqual(destination.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
