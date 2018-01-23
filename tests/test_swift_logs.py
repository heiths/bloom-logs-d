from unittest import TestCase, mock
from bf.log_processor import process_log


class TestSwiftLogs(TestCase):
    @mock.patch('log_processor.SwiftLogs.get_log_data',
                return_value=["Jul  4 22:00:12 127.0.0.1 proxy-server: 23.111.128.6 172.24.8.28 "
                              "04/Jul/2017/22/00/12 DELETE /v1/JungleDisk_prod/swift HTTP/1.0 404"])
    def test_create_bloom_filter(self, mock_get_log):
        process_log("log_file")
        mock_get_log.assert_called_with("log_file")
