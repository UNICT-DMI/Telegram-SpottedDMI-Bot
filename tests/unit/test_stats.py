from modules.data import PostData
from modules.handlers.stats import REACTION, avg_callback

from pytest_mock import MockerFixture

def test_avg_callback(mocker: MockerFixture) -> None:
    # arrange
    mock_return = 1
    mock_param = "5"
    mocker.patch.object(PostData, "get_avg", return_value=mock_return)
    spy = mocker.spy(PostData, "get_avg")

    # act
    res1 = avg_callback("votes")
    res2 = avg_callback(mock_param)

    # assert
    assert res1 == (f"Gli spot ricevono in media {mock_return} voti")
    assert res2 == (f"Gli spot ricevono in media {mock_return} {REACTION[mock_param]}")
    assert spy.call_count == 2
    assert spy.spy_return == mock_return
