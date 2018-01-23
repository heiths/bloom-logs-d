from unittest import TestCase, mock


class TestBloomFilter(TestCase):
    @mock.patch('bf.log_processor.SwiftLogs.process_log')
    @mock.patch('bf.log_processor.SwiftLogs.get_recent_objects',
                return_value=["logfile1.gz", "logfile2.gz", "logfile3.gz", "logfile4.gz"])
    def test_create_recent(self, mock_obj, mock_create):
        file_list = mock_obj
        for f in file_list:
            mock_create.assert_called_with(f)
