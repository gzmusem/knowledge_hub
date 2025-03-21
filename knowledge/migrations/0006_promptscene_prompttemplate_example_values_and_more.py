# Generated by Django 5.1.7 on 2025-03-19 09:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0005_prompttemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromptScene',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='场景名称')),
                ('code', models.CharField(help_text='场景的唯一标识符，如：code_review', max_length=50, unique=True, verbose_name='场景代码')),
                ('description', models.TextField(blank=True, verbose_name='场景描述')),
                ('icon', models.CharField(blank=True, help_text='可选的图标标识', max_length=50, verbose_name='场景图标')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '提示词场景',
                'verbose_name_plural': '提示词场景',
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.AddField(
            model_name='prompttemplate',
            name='example_values',
            field=models.JSONField(blank=True, default=dict, help_text="变量的示例值，格式：{'变量名': '示例值'}", verbose_name='变量示例值'),
        ),
        migrations.AddField(
            model_name='prompttemplate',
            name='system_prompt',
            field=models.ForeignKey(blank=True, limit_choices_to={'template_type': 'system'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_prompts', to='knowledge.prompttemplate', verbose_name='关联的系统提示词'),
        ),
        migrations.AlterField(
            model_name='prompttemplate',
            name='template_type',
            field=models.CharField(choices=[('system', '系统提示词'), ('user', '用户提示词')], default='user', max_length=20, verbose_name='模板类型'),
        ),
        migrations.AlterField(
            model_name='prompttemplate',
            name='variables',
            field=models.JSONField(blank=True, default=dict, help_text="定义模板中使用的变量，格式：{'变量名': '变量说明'}", verbose_name='变量定义'),
        ),
        migrations.AddField(
            model_name='prompttemplate',
            name='scene',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates', to='knowledge.promptscene', verbose_name='所属场景'),
        ),
    ]
