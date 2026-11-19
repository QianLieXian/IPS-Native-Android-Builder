package io.github.qianliexian.ips.nativeapp;

import android.app.AlertDialog;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.Toast;

import com.unity3d.player.UnityPlayerActivity;

import java.util.concurrent.ConcurrentLinkedQueue;

public final class MainActivity extends UnityPlayerActivity {
    private final ConcurrentLinkedQueue<Integer> actions = new ConcurrentLinkedQueue<>();
    private Button cheatButton;
    private AlertDialog cheatDialog;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout container = mUnityPlayer.getFrameLayout();
        cheatButton = new Button(this);
        cheatButton.setText("★");
        cheatButton.setTextColor(Color.WHITE);
        cheatButton.setTextSize(17);
        cheatButton.setContentDescription("游戏内置作弊");
        cheatButton.setPadding(0, 0, 0, 0);
        cheatButton.setMinWidth(0);
        cheatButton.setMinHeight(0);
        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.OVAL);
        shape.setColor(0x9E211F1C);
        shape.setStroke(dp(1), 0x887C7167);
        cheatButton.setBackground(shape);
        cheatButton.setBackgroundTintList(ColorStateList.valueOf(0xB03A332D));
        FrameLayout.LayoutParams bounds = new FrameLayout.LayoutParams(dp(48), dp(48), Gravity.BOTTOM | Gravity.END);
        bounds.setMarginEnd(dp(12));
        bounds.bottomMargin = dp(12);
        cheatButton.setVisibility(View.GONE);
        cheatButton.setOnClickListener(view -> showCheats());
        container.addView(cheatButton, bounds);
    }

    @Override
    public void onWindowFocusChanged(boolean focused) {
        super.onWindowFocusChanged(focused);
        if (focused && Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                controller.hide(WindowInsets.Type.systemBars());
            }
        }
    }

    @Override
    protected String updateUnityCommandLineArguments(String arguments) {
        return (arguments == null ? "" : arguments + " ") + "-force-vulkan";
    }

    public void setCheatAvailability(boolean enabled) {
        runOnUiThread(() -> {
            cheatButton.setVisibility(enabled ? View.VISIBLE : View.GONE);
            if (!enabled) {
                actions.clear();
                if (cheatDialog != null) {
                    cheatDialog.dismiss();
                }
            }
        });
    }

    public int takeCheatAction() {
        Integer action = actions.poll();
        return action == null ? 0 : action;
    }

    public void reportCheatResult(boolean gold, String before, String after) {
        String label = gold ? "金币" : "声望";
        runOnUiThread(() -> Toast.makeText(this, label + "  " + before + " → " + after, Toast.LENGTH_SHORT).show());
    }

    private void showCheats() {
        String[] options = {
            "金币 +100　增加当前经营的金币",
            "金币 −100　扣除当前经营的金币",
            "声望 +10　提高当前经营的声望",
            "声望 −10　降低当前经营的声望"
        };
        cheatDialog = new AlertDialog.Builder(this)
            .setTitle("游戏内置作弊 · 原版 F9")
            .setItems(options, (dialog, index) -> actions.offer(index + 1))
            .setNegativeButton("关闭", null)
            .create();
        cheatDialog.setOnDismissListener(dialog -> cheatDialog = null);
        cheatDialog.show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}