from app.main import main


def test_main(capsys):
    main()
    captured = capsys.readouterr()
    assert "Tripzy" in captured.out
