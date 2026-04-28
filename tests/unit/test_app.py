from unittest.mock import MagicMock, patch

from bitnet_launcher.app import main


@patch("bitnet_launcher.app.sys")
@patch("bitnet_launcher.app.QApplication")
@patch("bitnet_launcher.app.build_palette")
@patch("bitnet_launcher.app.BitNetLauncher")
def test_main(mock_launcher, mock_palette, mock_qapp, mock_sys):
    mock_app_instance = MagicMock()
    mock_qapp.return_value = mock_app_instance

    mock_window_instance = MagicMock()
    mock_launcher.return_value = mock_window_instance

    main()

    mock_qapp.assert_called_once_with(mock_sys.argv)
    mock_app_instance.setApplicationName.assert_called_with("BitNet Launcher")
    mock_palette.assert_called_once_with(mock_app_instance)

    mock_launcher.assert_called_once()
    mock_window_instance.show.assert_called_once()

    mock_sys.exit.assert_called_once_with(mock_app_instance.exec())
