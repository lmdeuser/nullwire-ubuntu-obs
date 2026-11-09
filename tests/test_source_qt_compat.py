"""Compile the accessibility attribute boundary against Qt 6.10 and 6.11 APIs."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE='''QList<QAccessible::Attribute> Widget::attributeKeys() const {
	auto result = QList<QAccessible::Attribute>();
	if (rp()->accessibilityOrientation().has_value()) {
		result.append(QAccessible::Attribute::Orientation);
	}
	return result;
}

QVariant Widget::attributeValue(QAccessible::Attribute key) const {
	if (key == QAccessible::Attribute::Orientation) {
		if (const auto orientation = rp()->accessibilityOrientation()) {
			// Plain int by design: the UIA bridge reads this back with
			// QVariant::toInt(), and Qt::Orientation isn't a registered
			// metatype here - QVariant::fromValue() of it wouldn't round-trip.
			return int(*orientation);
		}
	}
	return QVariant();
}
'''
STUB='''#include <optional>
#ifndef QT_VERSION_CHECK
#define QT_VERSION_CHECK(major, minor, patch) ((major << 16) | (minor << 8) | patch)
#endif
namespace QAccessible {
enum class Attribute {
	Custom,
	Level,
	Locale,
#if QT_VERSION >= QT_VERSION_CHECK(6, 11, 0)
	Orientation,
#endif
};
}
namespace Qt { enum Orientation { Horizontal = 1, Vertical = 2 }; }
template<typename T> struct QList { void append(T) {} };
struct QVariant {
	QVariant() {}
	QVariant(int) {}
};
struct RoleParameters {
	std::optional<Qt::Orientation> accessibilityOrientation() const { return std::nullopt; }
};
struct Widget {
	RoleParameters parameters;
	RoleParameters *rp() const { return const_cast<RoleParameters*>(&parameters); }
	QList<QAccessible::Attribute> attributeKeys() const;
	QVariant attributeValue(QAccessible::Attribute key) const;
};
'''

class QtAccessibilityTests(unittest.TestCase):
    def test_orientation_attribute_matches_available_qt_api(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'Telegram/lib_ui/ui/accessible/ui_accessible_widget.cpp'
            source.parent.mkdir(parents=True)
            source.write_text(SOURCE)
            compatibility=ROOT/'packaging/source/debian/patches/qt-6.10-accessible-orientation.patch'
            if compatibility.exists():
                subprocess.run(['patch','--fuzz=0','-p1','-d',str(root),'-i',str(compatibility)],check=True,capture_output=True)
            harness=root/'harness.cpp'
            harness.write_text(STUB+source.read_text())
            for version in ['0x060A00','0x060B00']:
                result=subprocess.run(['c++','-std=c++20','-fsyntax-only','-DQT_VERSION='+version,str(harness)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,version+'\n'+result.stdout+result.stderr)

    def test_thanos_animation_respects_disabled_private_qt_api(self):
        source_text='''ThanosEffect::ThanosEffect(not_null<QWidget*> parent)
: _parent(parent)
, _animation([=] {
	if (_renderer && _renderer->failed()) {
		ThanosEffectFailedOnce = true;
		hideSurface();
		return;
	}
	if (const auto w = surfaceWidget()) {
		w->update();
	}
}) {
}
'''
        stub='''#define QT_VERSION 0x060A00
#define QT_VERSION_CHECK(major, minor, patch) ((major << 16) | (minor << 8) | patch)
struct QWidget {};
template<typename T> using not_null = T;
namespace Ui {
#if QT_VERSION >= QT_VERSION_CHECK(6, 7, 0) && !defined DESKTOP_APP_DISABLE_PRIVATE_QT_API
class ThanosEffectRenderer { public: bool failed() const { return false; } };
#else
class ThanosEffectRenderer;
#endif
struct Animation { template<typename T> Animation(T) {} };
struct Surface { void update() {} };
class ThanosEffect {
public:
	explicit ThanosEffect(not_null<QWidget*> parent);
private:
	void hideSurface() {}
	Surface *surfaceWidget() { return nullptr; }
	QWidget *_parent;
	ThanosEffectRenderer *_renderer = nullptr;
	Animation _animation;
};
bool ThanosEffectFailedOnce = false;
}
using namespace Ui;
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'Telegram/SourceFiles/ui/effects/thanos_effect.cpp'
            source.parent.mkdir(parents=True)
            source.write_text(source_text)
            compatibility=ROOT/'packaging/source/debian/patches/disable-private-qt-thanos.patch'
            if compatibility.exists():
                subprocess.run(['patch','--fuzz=0','-p1','-d',str(root),'-i',str(compatibility)],check=True,capture_output=True)
            harness=root/'thanos-harness.cpp'
            harness.write_text(stub+source.read_text())
            for disabled in [True,False]:
                command=['c++','-std=c++20','-fsyntax-only']
                if disabled:
                    command.append('-DDESKTOP_APP_DISABLE_PRIVATE_QT_API')
                result=subprocess.run([*command,str(harness)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,str(disabled)+'\n'+result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
