from stdimage import validators


class TestBaseSizeValidator:
    def test_init__none(self):
        assert validators.MinSizeValidator(None, None).limit_value == (
            float('inf'), float('inf')
        )


class TestMaxSizeValidator:
    def test_compare__inf(self):
        limit_value = float("inf"), float("inf")
        instance = validators.MaxSizeValidator(*limit_value)
        assert not instance.compare((300, 200), limit_value)

    def test_compare__eq(self):
        assert not validators.MaxSizeValidator(300, 200).compare((300, 200), (300, 200))

    def test_compare__gt(self):
        limit_value = 300, 200
        instance = validators.MaxSizeValidator(*limit_value)
        assert instance.compare((600, 400), limit_value)
        assert instance.compare((600, 200), limit_value)
        assert instance.compare((300, 400), limit_value)
        assert instance.compare((600, 100), limit_value)
        assert instance.compare((150, 400), limit_value)

    def test_compare__lt(self):
        limit_value = 300, 200
        instance = validators.MaxSizeValidator(*limit_value)
        assert not instance.compare((150, 100), (300, 200))
        assert not instance.compare((300, 100), (300, 200))
        assert not instance.compare((150, 200), (300, 200))


class TestMinSizeValidator:
    def test_compare__inf(self):
        limit_value = float("inf"), float("inf")
        instance = validators.MinSizeValidator(*limit_value)
        assert instance.compare((300, 200), limit_value)

    def test_compare__eq(self):
        assert not validators.MinSizeValidator(300, 200).compare((300, 200), (300, 200))

    def test_compare__gt(self):
        limit_value = 300, 200
        instance = validators.MinSizeValidator(*limit_value)
        assert not instance.compare((600, 400), limit_value)
        assert not instance.compare((600, 200), limit_value)
        assert not instance.compare((300, 400), limit_value)
        assert instance.compare((600, 100), limit_value)
        assert instance.compare((150, 400), limit_value)

    def test_compare__lt(self):
        limit_value = 300, 200
        instance = validators.MinSizeValidator(*limit_value)
        assert instance.compare((150, 100), (300, 200))
        assert instance.compare((300, 100), (300, 200))
        assert instance.compare((150, 200), (300, 200))
